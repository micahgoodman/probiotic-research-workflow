#!/usr/bin/env python3
"""Compiles strains/ into build/catalogue.csv, build/catalogue.md and build/coverage.md.

    python3 tools/build.py [--out build] [--root .]

The build does three things and nothing else:

  1. Runs validation and refuses to write if any error is found. The compiled
     views are the surface people read, so publishing from data known to be
     invalid is the one way a defect becomes invisible.

  2. Performs the two joins. A claim row stores impact_id and a shard stores
     strain_id; the display label, the body system, and every identity field come
     from vocabulary/outcomes.json and roster.json at this moment and are stored
     nowhere else. That is what makes a renamed label a one-file edit.

  3. Reports coverage, which is deliberately not validated. Which entities have no
     directory and which passes came back empty are facts about a normal
     intermediate state, not defects.

Never hand-edit build/ - it is regenerated from strains/.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
from datetime import date

from catalogue import (
    ALL_SHARD,
    BODY_SYSTEMS,
    POPULATIONS,
    SLUG,
    Catalogue,
    Progress,
    Shard,
    all_progress,
    display_name,
    entity_progress,
    oldest_review_date,
    plural,
    systems_for_shard,
    unsearched_ids,
    write_text,
)
from validate import validate

CSV_COLUMNS = [
    "strain_id",
    "strain_designation",
    "entity_type",
    "preparation",
    "genus",
    "species",
    "body_system",
    "impact_id",
    "health_impact",
    "direction",
    "population",
    "population_detail",
    "study_type",
    "evidence_tier",
    "n_studies",
    "n_participants",
    "independently_replicated",
    "consistency",
    "effect_size",
    "bias_assessment",
    "industry_funded",
    "tier_rationale",
    "dose",
    "duration",
    "delivery_format",
    "safety_flags",
    "sources",
    "shard",
    "last_reviewed",
    "notes",
]

TIER_KEY = (
    "**A** high (SR/meta-analysis, bias appraised) · **B** moderate (RCTs, no SR) · "
    "**C** low · **D** very low (case reports) · **P** preclinical (animal or in vitro)"
)


# --- ordering --------------------------------------------------------------------

# Everything below build() runs post-validation, so joins resolve and domains hold:
# rules 2 and 16 put every impact_id in the vocabulary with an in-scope body_system,
# rule 4 pins population, rules 5 and 14 make study_type and last_reviewed usable,
# rule 8 gives every entity a strain_id. Indexing directly keeps those guarantees
# load-bearing - if a validator bug ever lets bad data through, the build crashes
# here instead of publishing rows that silently sorted or joined to nothing.

SHARD_ORDER = [ALL_SHARD] + [SLUG[s] for s in BODY_SYSTEMS]


def _canonical(shards: list[Shard]) -> list[Shard]:
    """Directory order is alphabetical, which puts mechanistic before metabolic; the
    fixed body-system order is what lets two entities' sections be compared line by
    line."""
    return sorted(shards, key=lambda s: SHARD_ORDER.index(s.basename))


def _row_sort_key(cat: Catalogue):
    """Stable order so a rebuild diff shows real changes rather than reshuffling."""
    vocabulary_order = {oid: i for i, oid in enumerate(cat.outcomes)}

    def key(row: dict) -> tuple:
        return (
            BODY_SYSTEMS.index(row["body_system"]),
            vocabulary_order[row["impact_id"]],
            POPULATIONS.index(row["population"]),
        )

    return key


def joined_rows(cat: Catalogue) -> list[dict]:
    """One dict per claim, with identity and outcome joined in. The only place the
    two joins happen."""
    rows: list[dict] = []
    key = _row_sort_key(cat)
    for entity in cat.entities:
        strain_id = entity["strain_id"]
        entity_rows: list[dict] = []
        for shard in cat.shards_for(strain_id):
            for claim in shard.claims:
                impact_id = claim["impact_id"]
                entity_rows.append(
                    {
                        "strain_id": strain_id,
                        "strain_designation": entity.get("strain_designation", ""),
                        "entity_type": entity["entity_type"],
                        "preparation": entity["preparation"],
                        "genus": entity.get("genus", ""),
                        "species": entity.get("species", ""),
                        "body_system": cat.body_system(impact_id),
                        "impact_id": impact_id,
                        "health_impact": cat.label(impact_id),
                        "direction": claim["direction"],
                        "population": claim["population"],
                        "population_detail": claim.get("population_detail", ""),
                        "study_type": "; ".join(claim["study_type"]),
                        "evidence_tier": claim["evidence_tier"],
                        "n_studies": claim.get("n_studies"),
                        "n_participants": claim.get("n_participants"),
                        "independently_replicated": claim["independently_replicated"],
                        "consistency": claim["consistency"],
                        "effect_size": claim.get("effect_size", ""),
                        "bias_assessment": claim["bias_assessment"],
                        "industry_funded": claim["industry_funded"],
                        "tier_rationale": claim.get("tier_rationale", ""),
                        "dose": claim.get("dose", ""),
                        "duration": claim.get("duration", ""),
                        "delivery_format": claim.get("delivery_format", ""),
                        "safety_flags": claim.get("safety_flags", ""),
                        "sources": "; ".join(claim.get("sources") or []),
                        "shard": f"{shard.basename}.json",
                        "last_reviewed": shard.last_reviewed,
                        "notes": claim.get("notes", ""),
                        "_claim": claim,
                    }
                )
        rows.extend(sorted(entity_rows, key=key))
    return rows


# --- catalogue.csv ---------------------------------------------------------------


def render_csv(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow({c: "" if row[c] is None else row[c] for c in CSV_COLUMNS})
    return buffer.getvalue()


# --- catalogue.md ----------------------------------------------------------------


def _claim_lines(row: dict) -> list[str]:
    """Only fields that carry something. An empty field printed as a separator reads
    as a measurement that came out blank."""
    claim = row["_claim"]
    lines: list[str] = []

    head = f"**{row['population']}** · {row['direction']} · tier **{row['evidence_tier']}**"
    if row["population_detail"]:
        head += f" — {row['population_detail']}"
    lines.append(head)

    evidence = []
    if row["effect_size"]:
        evidence.append(row["effect_size"])
    if claim.get("n_studies") is not None:
        evidence.append(f"{claim['n_studies']} stud{'y' if claim['n_studies'] == 1 else 'ies'}")
    if claim.get("n_participants") is not None:
        # "96 participants" for a mouse study reads as a clinical trial at a glance,
        # which is the exact conflation the humans/animals split exists to prevent.
        unit = {"humans": "participants", "animals": "animals"}.get(row["population"])
        evidence.append(
            f"{claim['n_participants']:,} {unit}" if unit else f"n = {claim['n_participants']:,}"
        )
    evidence.append(row["consistency"])
    evidence.append(f"independent replication: {row['independently_replicated']}")
    lines.append(" · ".join(evidence))

    practical = [v for v in (row["dose"], row["duration"], row["delivery_format"]) if v]
    if practical:
        lines.append(" · ".join(practical))

    provenance = [", ".join(claim["study_type"])]
    provenance.append(f"bias: {row['bias_assessment']}")
    provenance.append(f"industry funding: {row['industry_funded']}")
    lines.append(" · ".join(provenance))

    if row["tier_rationale"]:
        lines.append(f"*{row['tier_rationale']}*")
    if row["safety_flags"]:
        lines.append(f"**Safety:** {row['safety_flags']}")
    if row["notes"]:
        lines.append(row["notes"])
    if row["sources"]:
        lines.append(f"Sources: {row['sources']}")
    return lines


def _shard_label(shard: Shard) -> str:
    return "All systems" if shard.basename == ALL_SHARD else ", ".join(systems_for_shard(shard.basename))


def _entity_section(cat: Catalogue, entity: dict, rows: list[dict], progress: Progress) -> list[str]:
    strain_id = entity["strain_id"]
    out = [f"## {display_name(entity)}", ""]

    identity = f"`{strain_id}` · {entity['entity_type']} · {entity['preparation']}"
    if progress.depth:
        identity += f" · triaged {progress.depth}"
    block = [identity]

    aliases = entity.get("also_known_as") or []
    if aliases:
        block.append(f"Also known as: {', '.join(aliases)}")
    components = entity.get("component_strains") or []
    if components:
        block.append(f"Components: {'; '.join(components)}")

    shards = _canonical(cat.shards_for(strain_id))
    block.append(
        f"Reviewed {oldest_review_date(shards)} "
        f"(oldest of {plural(len(shards), 'pass', 'passes')})"
    )
    incomplete = []
    if progress.missing:
        incomplete.append(
            f"{', '.join(progress.missing)} "
            f"{'pass has' if len(progress.missing) == 1 else 'passes have'} not run"
        )
    if progress.unfinished:
        incomplete.append(
            f"{', '.join(progress.unfinished)} still "
            f"{'owes' if len(progress.unfinished) == 1 else 'owe'} targeted searches"
        )
    if incomplete:
        block.append(f"**Incomplete:** {'; '.join(incomplete)}.")
    # Hard line breaks: without the trailing double-space, markdown folds the whole
    # identity block into one run-on paragraph.
    out.extend(f"{line}  " for line in block)
    out.append("")

    for shard in shards:
        if not shard.pass_summary:
            continue
        out.append(f"> **{_shard_label(shard)}.** {shard.pass_summary}")
        out.append("")

    if not rows:
        out.append("No gradeable claims recorded. The passes above ran and found nothing")
        out.append("that met the grading bar; this is a finding, not a gap.")
        out.append("")

    current_system = None
    current_impact = None
    for row in rows:
        if row["body_system"] != current_system:
            current_system = row["body_system"]
            current_impact = None
            out.append(f"### {current_system}")
            out.append("")
        if row["impact_id"] != current_impact:
            current_impact = row["impact_id"]
            out.append(f"#### {row['health_impact']}")
            out.append("")
            out.append(f"`{current_impact}`")
            out.append("")
        lines = _claim_lines(row)
        out.append(f"- {lines[0]}")
        out.extend(f"  - {line}" for line in lines[1:])
        out.append("")

    searched = [s for s in shards if s.searched_empty]
    if searched:
        # "Looked and could not write a row" is decision-relevant to a reader: it is
        # the difference between absent evidence and an absent search.
        out.append("**Searched, nothing gradeable found:**")
        out.append("")
        out.extend(
            f"- {_shard_label(s)}: {'; '.join(cat.label(i) or i for i in s.searched_empty)}"
            for s in searched
        )
        out.append("")

    noted = [s for s in shards if s.gaps]
    if noted:
        out.append("**Gaps noted:**")
        out.append("")
        out.extend(f"- {_shard_label(s)}: {s.gaps}" for s in noted)
        out.append("")
    return out


def render_catalogue_md(cat: Catalogue, rows: list[dict], today: str) -> str:
    by_entity: dict[str, list[dict]] = {}
    for row in rows:
        by_entity.setdefault(row["strain_id"], []).append(row)

    researched = [e for e in cat.entities if cat.shards_for(e["strain_id"])]
    out = [
        "# Probiotic Evidence Catalogue",
        "",
        f"{plural(len(rows), 'claim')} across "
        f"{plural(len(researched), 'researched entity', 'researched entities')} "
        f"of {len(cat.entities)} on the roster. Built {today}.",
        "",
        "Generated by `tools/build.py` from `strains/`. Identity is joined from "
        "`roster.json`, outcome labels and body systems from "
        "`vocabulary/outcomes.json`. Do not hand-edit.",
        "",
        f"Tiers: {TIER_KEY}",
        "",
        "Human and preclinical evidence are separate ladders. Where an outcome carries "
        "both, they appear as separate lines under one heading: preclinical work never "
        "raises a human tier, and a human finding never suppresses the animal row.",
        "",
        "What this is, and is not: an evidence map graded from abstracts and published "
        "systematic reviews. Full-text critical appraisal is delegated to the review "
        "literature, which is why tier A requires one. Doses and effect sizes are as "
        "the sources reported them, not verified against full texts. Abstracts "
        "overstate positive results and the catalogue inherits that; recorded nulls "
        "and the tier ladder are the counterweight, not a cure. A study that never "
        "confirms its exact strain is excluded, so the table errs toward missing "
        "evidence rather than misattributing it — and an absent row means no pass "
        "found or searched the outcome, never that the effect is disproven.",
        "",
        "See `coverage.md` for what has not been researched yet.",
        "",
        "---",
        "",
    ]
    if not researched:
        out.append("Nothing researched yet. `coverage.md` lists what is outstanding.")
        out.append("")
        return "\n".join(out)

    for entity in researched:
        progress = entity_progress(cat, entity["strain_id"])
        out.extend(_entity_section(cat, entity, by_entity.get(entity["strain_id"], []), progress))
        out.append("---")
        out.append("")
    return "\n".join(out)


# --- coverage.md -----------------------------------------------------------------


def render_coverage_md(cat: Catalogue, warnings, today: str) -> str:
    progress = all_progress(cat)
    by_state: dict[str, list[Progress]] = {}
    for item in progress:
        by_state.setdefault(item.state, []).append(item)

    names = {e["strain_id"]: display_name(e) for e in cat.entities if e.get("strain_id")}
    out = [
        "# Coverage report",
        "",
        f"Built {today} by `tools/build.py`. Answers \"is the catalogue done?\" without "
        "opening every directory.",
        "",
        "None of this is a validation failure. A half-researched catalogue is a normal "
        "intermediate state, so coverage is reported rather than enforced.",
        "",
        "| State | Entities | Meaning |",
        "|---|---|---|",
    ]
    meanings = [
        ("complete", "every pass triage called for has been written"),
        ("in_progress", "passes still owed - missing, or written but owing targeted searches"),
        ("not_started", "triaged, no research pass yet"),
        ("untriaged", "no depth budget, so nobody has decided how many passes it gets"),
        ("dropped", "triaged as `drop`; should be moved to `excluded_entities`"),
    ]
    for state, meaning in meanings:
        out.append(f"| {state} | {len(by_state.get(state, []))} | {meaning} |")
    n_claims = sum(item.n_claims for item in progress)
    out += [
        f"| **total** | **{len(progress)}** | "
        f"{plural(len(cat.shards), 'shard')}, {plural(n_claims, 'claim')} |",
        "",
    ]

    def section(title: str, lines: list[str]) -> None:
        if not lines:
            return
        out.append(f"## {title} ({len(lines)})")
        out.append("")
        out.extend(lines)
        out.append("")

    def owed(item: Progress) -> str:
        parts = []
        if item.missing:
            parts.append(f"**missing: {', '.join(item.missing)}**")
        if item.unfinished:
            parts.append(f"**unfinished: {', '.join(item.unfinished)}**")
        return " · ".join(parts)

    section(
        "In progress",
        [
            f"- `{i.strain_id}` — {names.get(i.strain_id, '')}  \n"
            f"  written: {', '.join(i.present)} · {owed(i)}"
            for i in by_state.get("in_progress", [])
        ],
    )
    section(
        "Triaged, research not started",
        [
            # A not_started entity always has a budget: expected=None routes to
            # untriaged before this state can be reached.
            f"- `{i.strain_id}` — depth `{i.depth}`, expects "
            f"{', '.join(f'{s}.json' for s in i.expected)}"
            for i in by_state.get("not_started", [])
        ],
    )
    section(
        "Complete",
        [
            f"- `{i.strain_id}` — {plural(len(i.present), 'pass', 'passes')}, "
            f"{plural(i.n_claims, 'claim')}"
            for i in by_state.get("complete", [])
        ],
    )
    section(
        "Awaiting triage",
        [f"- `{i.strain_id}` — {names.get(i.strain_id, '')}" for i in by_state.get("untriaged", [])],
    )
    section(
        "Triaged as drop, still on the roster",
        [
            f"- `{i.strain_id}` — run `python3 tools/triage.py drop {i.strain_id} \"<reason>\"`"
            for i in by_state.get("dropped", [])
        ],
    )

    empty_passes = [
        f"- `{i.strain_id}/{basename}.json`"
        for i in progress
        for basename in i.empty_passes
    ]
    if empty_passes:
        out.append(f"## Passes that ran and found nothing ({len(empty_passes)})")
        out.append("")
        out.append(
            "A shard with `claims: []` means the pass ran and came back empty, which is "
            "different from a pass that has not run. The distinction is the whole reason "
            "a pass always writes its shard."
        )
        out.append("")
        out.extend(empty_passes)
        out.append("")

    searched_lines = [
        f"- `{s.dir_name}/{s.basename}.json` — {', '.join(s.searched_empty)}"
        for s in cat.shards
        if s.searched_empty
    ]
    if searched_lines:
        n_searched = sum(len(s.searched_empty) for s in cat.shards)
        out.append(f"## Searched, no row to write ({n_searched})")
        out.append("")
        out.append(
            "Ids a pass individually searched and could not write a row for - the "
            "id-level version of the empty pass. An absent row for one of these means "
            "someone looked; an absent row for anything else means nobody has."
        )
        out.append("")
        out.extend(searched_lines)
        out.append("")

    debt_lines = []
    for item in progress:
        by_name = {s.basename: s for s in cat.shards_for(item.strain_id)}
        for basename in item.unfinished:
            ids = unsearched_ids(cat, by_name[basename])
            debt_lines.append(f"- `{item.strain_id}/{basename}.json` — {', '.join(ids)}")
    if debt_lines:
        out.append(f"## Deep passes still owing targeted searches ({len(debt_lines)})")
        out.append("")
        out.append(
            "A deep pass owes a targeted search per allowed id, each ending in a claim "
            "row or a `searched_empty` entry; the remainder is derived, so it cannot be "
            "forgotten shut. These shards are written but owe the ids listed - the "
            "entity reads in progress, and the research stage re-opens exactly this debt."
        )
        out.append("")
        out.extend(debt_lines)
        out.append("")

    swept_lines = []
    for item in progress:
        if item.depth not in ("standard", "light"):
            continue
        all_shard = next(
            (s for s in cat.shards_for(item.strain_id) if s.basename == ALL_SHARD), None
        )
        if all_shard is None:
            continue
        remainder = unsearched_ids(cat, all_shard)
        if remainder:
            swept_lines.append(
                f"- `{item.strain_id}` — {len(remainder)} of {len(cat.outcomes)} "
                "in-scope outcomes covered by the general sweep only"
            )
    if swept_lines:
        out.append(f"## Covered by the general sweep only ({len(swept_lines)})")
        out.append("")
        out.append(
            "A standard or light pass owes its known-for areas plus a general sweep, "
            "not a targeted search per id. Counted rather than enumerated because this "
            "is the budget working as designed, not debt."
        )
        out.append("")
        out.extend(swept_lines)
        out.append("")

    proposed = [
        f"- `{shard.rel}` — **{p.get('suggested_label', '?')}** "
        f"({p.get('suggested_body_system', '?')}): {p.get('rationale', '')}"
        for shard in cat.shards
        for p in shard.proposed_impacts
    ]
    if proposed:
        out.append(f"## Proposed impacts awaiting reconciliation ({len(proposed)})")
        out.append("")
        out.append(
            "Outcomes a research pass found with no matching `impact_id`. Adding one to "
            "`vocabulary/outcomes.json` is a deliberate step, never done by the pass that "
            "proposed it."
        )
        out.append("")
        out.extend(proposed)
        out.append("")

    unexpected = [
        f"- `{i.strain_id}` — {', '.join(f'{s}.json' for s in i.unexpected)}"
        for i in progress
        if i.unexpected
    ]
    if unexpected:
        n_unexpected = sum(len(i.unexpected) for i in progress)
        out.append(f"## Shards present but not expected ({n_unexpected})")
        out.append("")
        out.append(
            "Triage depth changed after the research ran, or a pass wrote a shard the "
            "depth budget does not call for. The claims are still valid; the pass plan "
            "and the data disagree about which passes this entity gets."
        )
        out.append("")
        out.extend(unexpected)
        out.append("")

    if warnings:
        out.append(f"## Validation warnings ({len(warnings)})")
        out.append("")
        out.append(
            "Not rule violations - these do not block a build. They are fields the tier "
            "rules lean on, and triage or vocabulary inconsistencies that become bad "
            "research passes rather than bad rows."
        )
        out.append("")
        out.extend(f"- `{w.where}` — {w.message}" for w in warnings)
        out.append("")

    return "\n".join(out)


# --- entry point -----------------------------------------------------------------


def build(cat: Catalogue, out_dir: str, today: str | None = None) -> tuple[bool, list[str]]:
    """Returns (wrote_anything, messages). Writes nothing if validation fails."""
    today = today or date.today().isoformat()
    report = validate(cat)
    if not report.ok:
        return False, [str(f) for f in report.errors]

    rows = joined_rows(cat)
    write_text(os.path.join(out_dir, "catalogue.csv"), render_csv(rows))
    write_text(os.path.join(out_dir, "catalogue.md"), render_catalogue_md(cat, rows, today))
    write_text(os.path.join(out_dir, "coverage.md"), render_coverage_md(cat, report.warnings, today))

    researched = sum(1 for e in cat.entities if cat.shards_for(e["strain_id"]))
    return True, [
        f"{plural(len(rows), 'claim')} from {plural(len(cat.shards), 'shard')} "
        f"across {plural(researched, 'entity', 'entities')}",
        f"{plural(len(report.warnings), 'validation warning')} (see coverage.md)",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="catalogue root (default: $CATALOGUE_ROOT or repo)")
    parser.add_argument("--out", help="output directory (default: <root>/build)")
    args = parser.parse_args(argv)

    cat = Catalogue.load(args.root)
    out_dir = args.out or os.path.join(cat.root, "build")
    wrote, messages = build(cat, out_dir)

    if not wrote:
        print(f"build refused: {plural(len(messages), 'validation error')}\n")
        for message in messages:
            print(f"  {message}")
        print("\nNothing written. The compiled views are what people read, so they are")
        print("never generated from data already known to be wrong.")
        if os.path.exists(os.path.join(out_dir, "catalogue.csv")):
            print(f"{out_dir}/ still holds the previous build, which predates these")
            print("errors and is now stale.")
        return 1

    for message in messages:
        print(message)
    print(f"\nwrote {out_dir}/catalogue.csv, catalogue.md, coverage.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
