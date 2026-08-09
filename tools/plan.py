#!/usr/bin/env python3
"""What to work on next, and what one entity's research passes are allowed to contain.

    python3 tools/plan.py                 progress, plus the next entity for each stage
    python3 tools/plan.py <strain_id>     identity, triage verdict, and one block per
                                          pass listing the impact_ids that pass may use

The per-pass impact_id list is the point of this tool. Validation rule 11 rejects a
claim filed outside its body system's shard, and rule 2 rejects an invented
impact_id; printing the allowed set up front means a pass satisfies both by reading
rather than by guessing and being corrected afterwards.
"""

from __future__ import annotations

import argparse
import sys

from catalogue import (
    ALL_SHARD,
    BODY_SYSTEMS,
    Catalogue,
    all_progress,
    display_name,
    entity_progress,
    plural,
    systems_for_shard,
    unsearched_ids,
)

# Display order for the five progress states, shared by the count table and any
# future per-state listing. entity_progress produces exactly these.
STATES = ("complete", "in_progress", "not_started", "untriaged", "dropped")


def next_to_research(cat: Catalogue) -> str | None:
    """Finish what is started before starting something else.

    A catalogue of half-researched entities is worse than a smaller finished one:
    every entity looks present in the readable view while carrying only the body
    systems someone got to first.
    """
    progress = all_progress(cat)
    for state in ("in_progress", "not_started"):
        for item in progress:
            if item.state == state:
                return item.strain_id
    return None


def next_to_triage(cat: Catalogue) -> str | None:
    for item in all_progress(cat):
        if item.state == "untriaged":
            return item.strain_id
    return None


def same_species_entities(cat: Catalogue, entity: dict) -> list[tuple[str, str]]:
    """Roster and excluded entities sharing this entity's species.

    Most confusable strains are not exotic: they are other catalogue entities under
    the same species name, and crediting one of their studies here double-counts it
    inside the catalogue. Derived from the roster so there is no second list to
    maintain. Excluded entities match by label prefix - an exclusion keeps only its
    label - and they stay confusable after leaving the roster, more so, because
    their studies then belong to no entity at all. Off-roster confusables stay in
    triage_notes, and the per-study identity check covers strains nobody has met.
    """
    genus = entity.get("genus") or ""
    species = entity.get("species") or ""
    if not genus or not species or "multiple" in (genus, species):
        return []
    sid = entity.get("strain_id")
    rows = [
        (e.get("strain_id") or "?", display_name(e))
        for e in cat.entities
        if e.get("strain_id") != sid
        and e.get("genus") == genus
        and e.get("species") == species
    ]
    prefix = f"{genus} {species} "
    rows += [
        (x.get("strain_id") or "?", str(x.get("label") or "").strip())
        for x in cat.excluded_entities
        if str(x.get("label") or "").startswith(prefix)
    ]
    return rows


def print_status(cat: Catalogue) -> None:
    progress = all_progress(cat)
    counts = {state: 0 for state in STATES}
    for item in progress:
        counts[item.state] += 1

    n_claims = sum(item.n_claims for item in progress)
    print(f"{len(progress)} roster entities, {len(cat.excluded_entities)} excluded\n")
    print(f"  {'triaged':<14}{len(progress) - counts['untriaged']:>4} / {len(progress)}")
    for state in STATES:
        print(f"  {state:<14}{counts[state]:>4}")
    print(f"\n  {plural(len(cat.shards), 'shard')}, {plural(n_claims, 'claim')}")

    triage_next = next_to_triage(cat)
    research_next = next_to_research(cat)
    print(f"\n  next triage:    {triage_next or '(none outstanding)'}")
    if research_next:
        item = entity_progress(cat, research_next)
        owed = [f"missing {', '.join(item.missing)}"] if item.missing else []
        owed += [f"unfinished {', '.join(item.unfinished)}"] if item.unfinished else []
        detail = f"{item.state}, {'; '.join(owed)}" if owed else item.state
        print(f"  next research:  {research_next}  ({detail})")
    elif triage_next:
        print("  next research:  (none - triage has not reached an entity yet)")
    else:
        print("  next research:  (none outstanding)")

    stale = [item for item in progress if item.unexpected]
    if stale:
        print("\n  shards no longer expected (triage depth changed?):")
        for item in stale:
            print(f"    {item.strain_id}: {', '.join(item.unexpected)}")


def print_entity(cat: Catalogue, strain_id: str) -> int:
    # Exit codes: 0 when the question was answered - excluded, untriaged and
    # unreadable-depth are all answers - and 1 only when it could not be, so a
    # wrapper script can tell "look at the output" from "no such id".
    entity = cat.entity_by_id.get(strain_id)
    if entity is None:
        excluded = cat.excluded_by_id.get(strain_id)
        if excluded:
            print(f"{strain_id} is in excluded_entities, not on the roster.")
            print(f"  {excluded.get('label', '')}")
            print(f"  reason: {excluded.get('reason', '')}")
            return 0
        print(f"{strain_id} is on neither roster list. Check the id in roster.json.")
        return 1

    print(f"\n{strain_id}")
    print(f"  {display_name(entity)}")
    print(f"  {entity.get('entity_type')} | {entity.get('preparation')}")
    aliases = entity.get("also_known_as") or []
    if aliases:
        # Legacy genus names matter more than they look: the 2020 Lactobacillus split
        # means a search under the current name misses much of the literature.
        print(f"  also known as: {' | '.join(aliases)}")
    components = entity.get("component_strains") or []
    if components:
        print(f"  components: {'; '.join(components)}")
    print(f"  known for: {entity.get('known_for', '')}")
    print(f"  roster source: {entity.get('roster_source', '')}")

    siblings = same_species_entities(cat, entity)
    if siblings:
        print("  same species, different entity - a study of theirs is never credited here:")
        for sibling_id, name in siblings:
            print(f"    {sibling_id}  ({name})")

    triage_entry = cat.triage_by_id.get(strain_id)
    if triage_entry is None:
        print("\n  NOT TRIAGED. The pass plan comes from triage depth, so run the triage")
        print("  stage for this entity first: /catalogue-triage " + strain_id)
        return 0

    # The counts are optional on a drop entry; only present ones are shown.
    verdict = [f"triage: {triage_entry.get('depth')}"]
    if triage_entry.get("n_systematic_reviews") is not None:
        verdict.append(f"{triage_entry['n_systematic_reviews']} SRs")
    if triage_entry.get("n_human_trials") is not None:
        verdict.append(f"{triage_entry['n_human_trials']} human trials")
    print("\n  " + " | ".join(verdict))
    areas = triage_entry.get("outcome_areas") or []
    print(f"  outcome areas: {', '.join(areas) if areas else '(none recorded)'}")
    if triage_entry.get("has_preclinical_only_areas"):
        print("  has claims resting on preclinical work alone")
    if triage_entry.get("triage_notes"):
        print(f"  notes: {triage_entry['triage_notes']}")

    progress = entity_progress(cat, strain_id)
    if progress.state == "dropped":
        print("\n  Triaged as `drop`. It owes no research passes; move it to")
        print("  excluded_entities with: python3 tools/triage.py drop " + strain_id + ' "<reason>"')
        return 0

    if progress.expected is None:
        print(f"\n  Triage depth {progress.depth!r} is not light, standard, deep or drop,")
        print("  so no pass plan can be stated. Fix the depth in triage.json, or re-run")
        print("  the triage stage: /catalogue-triage " + strain_id)
        return 0

    expected = progress.expected
    print(f"\n  passes ({len(expected)}), {len(progress.present)} written:\n")
    for basename in expected:
        systems = systems_for_shard(basename)
        done = basename in progress.present
        unfinished = basename in progress.unfinished
        mark = "~" if unfinished else ("x" if done else " ")
        label = "all six systems" if basename == ALL_SHARD else ", ".join(systems)
        print(f"  [{mark}] strains/{strain_id}/{basename}.json   ({label})")
        if done:
            shard = next(s for s in cat.shards_for(strain_id) if s.basename == basename)
            print(f"        written {shard.last_reviewed}, {plural(len(shard.claims), 'claim')}")
            if unfinished:
                # A deep pass owes a targeted search per allowed id. Only the
                # remainder is printed: re-listing accounted ids would commission
                # the same search twice.
                owed = unsearched_ids(cat, shard)
                print(
                    f"        unfinished - targeted search still owed for "
                    f"{plural(len(owed), 'impact_id')}:"
                )
                for oid in owed:
                    print(f"          {oid:<32} {(cat.outcomes.get(oid) or {}).get('label', '')}")
                print()
            continue
        outcomes = sorted(
            cat.outcomes_in(systems),
            key=lambda o: (BODY_SYSTEMS.index(o["body_system"]), o["id"]),
        )
        print(f"        impact_ids allowed in this shard ({len(outcomes)}):")
        for outcome in outcomes:
            print(f"          {outcome['id']:<32} {outcome.get('label', '')}")
        print()

    if progress.unexpected:
        print(f"  shards present but not expected: {', '.join(progress.unexpected)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("strain_id", nargs="?", help="show this entity's pass plan")
    parser.add_argument("--root", help="catalogue root (default: $CATALOGUE_ROOT or repo)")
    args = parser.parse_args(argv)

    cat = Catalogue.load(args.root)
    if cat.parse_errors:
        for rel, message in cat.parse_errors:
            print(f"cannot read {rel}: {message}")
        return 1
    if args.strain_id:
        return print_entity(cat, args.strain_id)
    print_status(cat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
