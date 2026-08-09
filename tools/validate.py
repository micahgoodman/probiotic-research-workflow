#!/usr/bin/env python3
"""Checks the invariants in SCHEMA.md "Validation rules".

Two classes of finding, kept apart on purpose:

  errors    The 16 documented rules, plus two structural labels that precede them:
            `parse` (a file the loader cannot read as its documented shape) and
            `shape` (a field or entry that does not have its documented type).
            A structure that cannot be read cannot be validated, only reported -
            silently coercing it to an empty one once let a destroyed roster
            validate cleanly. Any error blocks the build.

  warnings  Everything else worth saying: prose the rules cannot check, missing
            fields the tier rules lean on, triage values that are readable but
            unhelpful. Reported and counted, never blocking, because a
            half-researched catalogue is a normal intermediate state. The line is
            whether the defect is representable in a finished catalogue - see
            SCHEMA.md after rule 16.

Where a rule references a field's value ("tier A requires...", "study_type agrees
with population"), the value's domain is checked as part of that rule. An
unrecognised population would otherwise match none of rule 4's branches and
silently switch the rule off, which is worse than the typo it hides.

Shape checks read the raw file data, never the coercing Shard/Catalogue accessors:
a validator reading through those would validate the coercion, not the file.

Usage:
    python3 tools/validate.py [strain_id ...] [--strict] [--quiet]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from catalogue import (
    BIAS_VALUES,
    BODY_SYSTEMS,
    CLAIM_FIELDS,
    CONSISTENCY_VALUES,
    DEPTHS,
    DIRECTIONS,
    ENTITY_TYPES,
    EXCLUSION_FIELDS,
    FUNDING_VALUES,
    IDENTITY_ONLY_FIELDS,
    OUTCOME_ONLY_FIELDS,
    POPULATIONS,
    PREPARATIONS,
    PRECLINICAL_POPULATIONS,
    REPLICATION_VALUES,
    ROSTER_FIELDS,
    SHARD_FIELDS,
    STUDY_TYPE_ORDER,
    STUDY_TYPE_RANK,
    TIERS,
    TRIAGE_FIELDS,
    Catalogue,
    is_real_date,
    plural,
    shard_basename,
)


@dataclass(frozen=True)
class Finding:
    rule: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.rule:>6} | {self.where} | {self.message}"


class Report:
    def __init__(self) -> None:
        self.errors: list[Finding] = []
        self.warnings: list[Finding] = []

    def error(self, rule: int | str, where: str, message: str) -> None:
        label = f"rule {rule}" if isinstance(rule, int) else str(rule)
        self.errors.append(Finding(label, where, message))

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(Finding("warn", where, message))

    @property
    def ok(self) -> bool:
        return not self.errors


def _unknown_keys(obj: dict, known: list[str]) -> list[str]:
    """Keys outside the schema. Leading-underscore keys are annotations, not data."""
    return sorted(k for k in obj if k not in known and not k.startswith("_"))


def _check_text(report: Report, where: str, field_name: str, value) -> None:
    """Shape of one free-text field: a single-line string, or absent.

    Single-line because every one of these lands in a markdown list item, a
    blockquote, or a CSV cell - a line break escapes the structure and the second
    line renders outside the row it belongs to, from data that read as valid.
    """
    if value is None:
        return
    if not isinstance(value, str):
        report.error("shape", where, f"{field_name} must be a string, got {value!r}")
    elif "\n" in value or "\r" in value:
        report.error(
            "shape",
            where,
            f"{field_name} must be a single line; a line break escapes the list "
            "item, blockquote, or cell it renders inside",
        )


# --- roster ----------------------------------------------------------------------


def check_roster(cat: Catalogue, report: Report, only: set[str] | None) -> None:
    entities_raw = cat.roster.get("entities")
    if not isinstance(entities_raw, list):
        report.error(
            "shape",
            "roster.json",
            "entities must be an array of entities"
            + ("" if entities_raw is None else f", got {entities_raw!r:.60}"),
        )
        entities_raw = []

    seen: set[str] = set()
    for index, entity in enumerate(entities_raw):
        if not isinstance(entity, dict):
            # Dropped silently, a non-object entity defeats rule 8's guarantee that
            # every roster decision is auditable - the entry exists in the file and
            # nowhere else.
            report.error("shape", "roster.json", f"entities[{index}] is not an object: {entity!r:.60}")
            continue
        sid = entity.get("strain_id")
        where = sid if isinstance(sid, str) and sid else f"entities[{index}]"

        if not isinstance(sid, str) and sid is not None:
            report.error("shape", where, f"strain_id must be a string, got {sid!r}")
            sid = None

        # Rule 8 exists so every roster decision is auditable. A missing or repeated
        # primary key defeats that just as thoroughly as a missing source does: the
        # second entry for an id is unreachable through the join and its claims would
        # attach to the first one's identity.
        if not sid:
            report.error(8, where, "entity has no strain_id")
        elif sid in seen:
            report.error(8, where, "duplicate strain_id in entities")
        if sid:
            seen.add(sid)

        if only and sid not in only:
            continue

        for field_name in ("genus", "species", "strain_designation", "known_for", "roster_source"):
            value = entity.get(field_name)
            if value is not None and not isinstance(value, str):
                report.error("shape", where, f"{field_name} must be a string, got {value!r}")
        for field_name in ("also_known_as", "component_strains"):
            value = entity.get(field_name)
            if value is not None and (
                not isinstance(value, list) or any(not isinstance(v, str) for v in value)
            ):
                # A bare string here joins character-by-character in every view:
                # "Also known as: L, a, c, t, o, ..."
                report.error(
                    "shape", where, f"{field_name} must be a list of strings, got {value!r:.60}"
                )

        source = entity.get("roster_source")
        if not (isinstance(source, str) and source.strip()):
            report.error(8, where, "empty roster_source - the entity is unauditable")

        entity_type = entity.get("entity_type")
        if entity_type not in ENTITY_TYPES:
            report.error(9, where, f"entity_type {entity_type!r} not in {ENTITY_TYPES}")
        else:
            has_components = bool(entity.get("component_strains"))
            if has_components != (entity_type == "product"):
                report.error(
                    9,
                    where,
                    "component_strains must be non-empty if and only if entity_type "
                    f"is 'product' (entity_type={entity_type!r}, "
                    f"component_strains={'present' if has_components else 'empty'})",
                )

        if entity.get("preparation") not in PREPARATIONS:
            report.error(
                10, where, f"preparation {entity.get('preparation')!r} not in {PREPARATIONS}"
            )

        for key in _unknown_keys(entity, ROSTER_FIELDS):
            report.warn(where, f"unknown roster field {key!r}")

    excluded_raw = cat.roster.get("excluded_entities")
    if excluded_raw is None:
        excluded_raw = []
    elif not isinstance(excluded_raw, list):
        report.error("shape", "roster.json", "excluded_entities must be an array of exclusions")
        excluded_raw = []

    excluded_seen: set[str] = set()
    for index, excluded in enumerate(excluded_raw):
        if not isinstance(excluded, dict):
            report.error(
                "shape", "roster.json", f"excluded_entities[{index}] is not an object: {excluded!r:.60}"
            )
            continue
        for field_name in EXCLUSION_FIELDS:
            value = excluded.get(field_name)
            if value is not None and not isinstance(value, str):
                report.error(
                    "shape",
                    f"excluded_entities[{index}]",
                    f"{field_name} must be a string, got {value!r}",
                )
        xid = str(excluded.get("strain_id") or "").strip()
        label = excluded.get("label") or "<no label>"
        if not xid:
            report.error(8, f"excluded:{str(label)[:60]}", "exclusion has no strain_id")
            continue
        if xid in excluded_seen:
            report.error(8, xid, "duplicate strain_id in excluded_entities")
        excluded_seen.add(xid)
        if not str(excluded.get("reason") or "").strip():
            report.warn(xid, "exclusion has no reason")
        for key in _unknown_keys(excluded, EXCLUSION_FIELDS):
            report.warn(xid, f"unknown exclusion field {key!r}")

    for xid in sorted(excluded_seen & seen):
        report.error(8, xid, "strain_id appears in both entities and excluded_entities")


# --- vocabulary ------------------------------------------------------------------


def check_vocabulary(cat: Catalogue, report: Report) -> None:
    """Rule 16: the vocabulary is a valid join table.

    Every claim resolves through this file, so a defect here never announces
    itself - it silently redefines rules 2 and 11 for every claim that joins
    through the damaged row. A duplicate id is the sharpest case: the last copy
    wins the join, so a claim filed correctly under the first copy's body system
    starts drawing false rule 11 errors.
    """
    where = "vocabulary/outcomes.json"
    outcomes_raw = cat.vocabulary.get("outcomes")
    if not isinstance(outcomes_raw, list):
        report.error("shape", where, "outcomes must be an array of outcomes")
        outcomes_raw = []

    seen: set[str] = set()
    for index, outcome in enumerate(outcomes_raw):
        if not isinstance(outcome, dict):
            report.error("shape", where, f"outcomes[{index}] is not an object: {outcome!r:.60}")
            continue
        oid = outcome.get("id")
        if not (isinstance(oid, str) and oid):
            report.error(16, where, f"outcomes[{index}] has no id, so no claim can join to it")
            continue
        if oid in seen:
            report.error(
                16,
                oid,
                "duplicate outcome id - the last copy silently wins every join, so "
                "rules 2 and 11 are redefined by file order",
            )
        seen.add(oid)
        system = outcome.get("body_system")
        if system not in BODY_SYSTEMS:
            report.error(
                16,
                oid,
                f"body_system {system!r} is not an in-scope body system; no shard may "
                "own this outcome, so rule 11 cannot place its claims",
            )
        label = outcome.get("label")
        if not (isinstance(label, str) and label.strip()):
            report.error(
                16, oid, "no usable label - the readable view would render an empty heading"
            )

    excluded_raw = cat.vocabulary.get("excluded_outcomes")
    if excluded_raw is None:
        excluded_raw = []
    elif not isinstance(excluded_raw, list):
        report.error("shape", where, "excluded_outcomes must be an array of outcomes")
        excluded_raw = []

    excluded_seen: set[str] = set()
    for index, outcome in enumerate(excluded_raw):
        if not isinstance(outcome, dict):
            report.error(
                "shape", where, f"excluded_outcomes[{index}] is not an object: {outcome!r:.60}"
            )
            continue
        oid = outcome.get("id")
        if not (isinstance(oid, str) and oid):
            report.error(
                16,
                where,
                f"excluded_outcomes[{index}] has no id - rule 2 matches exclusions by "
                "id, so the decision this entry records is unreachable",
            )
            continue
        excluded_seen.add(oid)

    for oid in sorted(seen & excluded_seen):
        report.error(
            16,
            oid,
            "in both outcomes and excluded_outcomes - in scope and out of scope at "
            "once, so rule 2 would accept and reject the same claim",
        )


# --- triage ----------------------------------------------------------------------


def check_triage(cat: Catalogue, report: Report, only: set[str] | None) -> None:
    """Rule 15, plus warnings about triage output that is readable but unusable.

    Triage output commissions research, so a defect here becomes a missing or
    misdirected research pass rather than a bad row.
    """
    if cat.triage is None:
        return
    entries = cat.triage.get("triage")
    if not isinstance(entries, list):
        # The file exists but its verdicts are unreadable, which is not the same as
        # "nobody has triaged yet" - every depth budget in it is lost.
        report.error("shape", "triage.json", "'triage' must be an array of entries")
        return

    seen: set[str] = set()
    roster_ids = set(cat.entity_by_id)
    excluded_ids = set(cat.excluded_by_id)
    for entry in entries:
        if not isinstance(entry, dict):
            report.error(15, "triage.json", f"entry is not an object: {entry!r}")
            continue
        sid = entry.get("strain_id")
        where = f"triage:{sid or '<no strain_id>'}"
        if not sid:
            report.error(15, "triage.json", "entry has no strain_id, so it names no entity")
            continue
        if sid in seen:
            report.error(
                15,
                where,
                "duplicate triage entry; the pass plan would depend on which one is read first",
            )
        seen.add(sid)
        if only and sid not in only:
            continue

        # A dropped entity keeps its triage record on purpose: it is the audit trail
        # showing the drop was confirmed rather than inferred. So resolving against
        # excluded_entities counts, and only naming neither list is a violation.
        if sid not in roster_ids and sid not in excluded_ids:
            report.error(
                15,
                where,
                "strain_id is on neither roster list - this budgets research passes for "
                "an entity that does not exist",
            )

        depth = entry.get("depth")
        if depth not in DEPTHS:
            report.warn(where, f"depth {depth!r} not in {DEPTHS}")
        elif depth == "drop" and sid in roster_ids:
            report.warn(
                where,
                "depth is 'drop' but the entity is still in roster entities - run "
                "`tools/triage.py drop` so it moves to excluded_entities with its id",
            )

        areas = entry.get("outcome_areas")
        if areas is None:
            if depth != "drop":
                report.warn(where, "no outcome_areas - the research stage has nowhere to look")
        elif not isinstance(areas, list):
            report.warn(where, "outcome_areas is not a list")
        else:
            for area in areas:
                if area not in BODY_SYSTEMS:
                    report.warn(
                        where,
                        f"outcome_areas names {area!r}, which is not an in-scope body system",
                    )
            repeated = sorted(
                {a for a in areas if isinstance(a, str) and areas.count(a) > 1}
            )
            if repeated:
                report.warn(where, f"outcome_areas names {repeated} more than once")

        for key in _unknown_keys(entry, TRIAGE_FIELDS):
            report.warn(where, f"unknown triage field {key!r}")


# --- shards ----------------------------------------------------------------------


def check_shard(
    cat: Catalogue,
    shard,
    report: Report,
    seen_claims: dict[tuple, str],
    *,
    is_template: bool = False,
) -> None:
    """Rules 2-7 and 11-14 within a shard; rule 1 accumulates through `seen_claims`.

    `is_template` exempts templates/shard.json from the two checks whose subject is a
    particular pass - its filename (rule 3) and its review date (rule 14) - and from
    warnings. It is a skeleton rather than a pass: its worked examples deliberately
    span every body system, and its placeholders are loud on purpose. Everything about
    the shape of a claim still applies, because a defect in the template is reproduced
    into every shard copied from it.

    Shape checks read `shard.data` raw. The Shard properties coerce a malformed field
    to an empty one for tolerant readers; a validator reading through them would
    validate the coercion, not the file - which is how a corrupted claim once
    vanished from validation, the claim count, and the build with no finding.
    """
    warnings = not is_template
    where_shard = shard.rel
    outcomes = cat.outcomes
    excluded_outcomes = cat.excluded_outcomes

    declared_raw = shard.data.get("body_systems")
    declared: list = []
    filename_checkable = False
    if not declared_raw:
        report.error(3, where_shard, "no body_systems - the pass declares no coverage")
    elif not isinstance(declared_raw, list):
        report.error(
            "shape", where_shard, f"body_systems must be a list, got {declared_raw!r}"
        )
    else:
        declared = declared_raw
        unknown_systems = [s for s in declared if s not in BODY_SYSTEMS]
        repeated = sorted({s for s in declared if isinstance(s, str) and declared.count(s) > 1})
        if unknown_systems:
            report.error(3, where_shard, f"body_systems names out-of-scope {unknown_systems}")
        if repeated:
            report.error(
                3,
                where_shard,
                f"body_systems lists {repeated} more than once - the declaration "
                "cannot be trusted to mean one system or all six",
            )
        filename_checkable = not unknown_systems and not repeated

    if not is_template and filename_checkable:
        expected = shard_basename(declared)
        if expected is None:
            report.error(
                3,
                where_shard,
                f"body_systems {declared} has no filename: a pass covers one "
                f"system or all {len(BODY_SYSTEMS)}",
            )
        elif shard.basename != expected:
            report.error(
                3,
                where_shard,
                f"filename does not match body_systems (expected {expected}.json)",
            )

    for banned in IDENTITY_ONLY_FIELDS:
        if banned in shard.data:
            report.error(3, where_shard, f"{banned!r} belongs in roster.json, not a shard")

    # --- rule 14: every pass carries a real date ----------------------------------
    if not is_template and not is_real_date(shard.data.get("last_reviewed")):
        report.error(
            14,
            where_shard,
            f"last_reviewed {shard.data.get('last_reviewed')!r} is not a real "
            "YYYY-MM-DD date. A placeholder sorts after every real date, so it would "
            "not become the entity's oldest pass and the entity would read fresher "
            "than it is",
        )

    summary = shard.data.get("pass_summary")
    _check_text(report, where_shard, "pass_summary", summary)
    _check_text(report, where_shard, "gaps", shard.data.get("gaps"))
    if warnings:
        if not (summary if isinstance(summary, str) else "").strip():
            report.warn(where_shard, "empty pass_summary")
        for key in _unknown_keys(shard.data, SHARD_FIELDS):
            report.warn(where_shard, f"unknown shard field {key!r}")

    proposed_raw = shard.data.get("proposed_impacts")
    if proposed_raw is not None and not isinstance(proposed_raw, list):
        report.error(
            "shape", where_shard, f"proposed_impacts must be a list, got {proposed_raw!r:.60}"
        )
        proposed_raw = []
    for index, proposed in enumerate(proposed_raw or []):
        if not isinstance(proposed, dict):
            report.error(
                "shape",
                where_shard,
                f"proposed_impacts[{index}] is not an object: {proposed!r:.60}",
            )
            continue
        for field_name in ("suggested_id", "suggested_label", "suggested_body_system", "rationale"):
            _check_text(
                report, where_shard, f"proposed_impacts[{index}].{field_name}",
                proposed.get(field_name),
            )
        if warnings:
            suggested = proposed.get("suggested_body_system")
            if suggested and suggested not in BODY_SYSTEMS:
                report.warn(
                    where_shard,
                    f"proposed impact suggests out-of-scope body system {suggested!r}; "
                    "excluded systems are dropped, not proposed",
                )

    claims_raw = shard.data.get("claims")
    if claims_raw is None:
        report.error(
            "shape",
            where_shard,
            "no claims array. A pass that found nothing writes claims: [] - that is "
            "a finding; a shard without the key does not say which happened",
        )
        claims_raw = []
    elif not isinstance(claims_raw, list):
        report.error("shape", where_shard, f"claims must be a list, got {claims_raw!r:.60}")
        claims_raw = []

    for index, claim in enumerate(claims_raw):
        if not isinstance(claim, dict):
            # Reported, never dropped: the row exists in the file, and a validator
            # that cannot read it must say so rather than validate the shard as if
            # the row were absent.
            report.error(
                "shape", where_shard, f"claims[{index}] is not an object: {claim!r:.60}"
            )
            continue
        impact_id = claim.get("impact_id")
        population = claim.get("population")
        where = f"{where_shard}[{index}] {impact_id}/{population}"

        impact_ok = impact_id is None or isinstance(impact_id, str)
        population_ok = population is None or isinstance(population, str)
        if not impact_ok:
            report.error("shape", where, f"impact_id must be a string, got {impact_id!r}")
        if not population_ok:
            report.error("shape", where, f"population must be a string, got {population!r}")

        # --- rule 1: (impact_id, population) unique across the whole entity ------
        # Guarded: a non-string makes the key unhashable, and the row already has a
        # shape error, so skipping dedup loses nothing.
        if impact_ok and population_ok:
            key = (impact_id, population)
            if key in seen_claims:
                report.error(
                    1,
                    where,
                    f"duplicate (impact_id, population); already in {seen_claims[key]}",
                )
            else:
                seen_claims[key] = shard.rel

        # --- rule 2: impact_id comes from the vocabulary ------------------------
        if impact_ok and impact_id not in outcomes:
            if impact_id in excluded_outcomes:
                report.error(
                    2,
                    where,
                    "impact_id is an excluded outcome - out of scope by decision, "
                    "so the pass records nothing",
                )
            else:
                report.error(2, where, "impact_id is not in vocabulary/outcomes.json")
        for banned in OUTCOME_ONLY_FIELDS:
            if banned in claim:
                report.error(
                    2,
                    where,
                    f"{banned!r} is joined from the vocabulary and must not be stored "
                    "on a claim",
                )

        # --- rule 11: the claim sits in the shard that owns its body system -----
        system = cat.body_system(impact_id) if impact_ok and impact_id in outcomes else None
        if system and declared and system not in declared:
            report.error(
                11,
                where,
                f"{system} claim in a shard declaring {declared}; it belongs to the "
                f"{system} pass",
            )

        # --- rule 4: study_type agrees with population --------------------------
        study_type = claim.get("study_type")
        if not isinstance(study_type, list):
            report.error("shape", where, f"study_type must be a list, got {study_type!r}")
            study_type = []
        if not population_ok:
            pass  # already a shape error; rule 4 would only restate it
        elif population not in POPULATIONS:
            report.error(
                4,
                where,
                f"population {population!r} not in {POPULATIONS}; the rule cannot be "
                "evaluated and every population-dependent check is off for this row",
            )
        elif population == "humans":
            non_human = [s for s in study_type if not (isinstance(s, str) and s.startswith("human_"))]
            if non_human:
                report.error(4, where, f"humans row carries non-human study_type {non_human}")
        elif population == "animals" and study_type != ["animal"]:
            report.error(4, where, f'animals row must be ["animal"], got {study_type}')
        elif population == "in_vitro" and study_type != ["in_vitro"]:
            report.error(4, where, f'in_vitro row must be ["in_vitro"], got {study_type}')

        # --- rule 5: canonical strongest-first order ----------------------------
        # isinstance first: the rank lookup hashes, so a non-string entry would be a
        # TypeError - a traceback where a finding belongs - instead of this error.
        unknown_types = [
            s for s in study_type if not isinstance(s, str) or s not in STUDY_TYPE_RANK
        ]
        if unknown_types:
            report.error(
                5, where, f"study_type {unknown_types} not in {STUDY_TYPE_ORDER}"
            )
        elif not study_type:
            # The order rule is what guarantees study_type[0] is the grading unit.
            # An empty list has no grading unit, so effect_size and the tier describe
            # nothing in particular.
            report.error(5, where, "study_type is empty - the row has no grading unit")
        else:
            ranks = [STUDY_TYPE_RANK[s] for s in study_type]
            if ranks != sorted(set(ranks)):
                report.error(
                    5,
                    where,
                    f"study_type is not in canonical strongest-first order without "
                    f"repeats: {study_type}",
                )

        # --- rules 6 and 7: tiers -----------------------------------------------
        tier = claim.get("evidence_tier")
        bias = claim.get("bias_assessment")
        if tier not in TIERS:
            report.error(7, where, f"evidence_tier {tier!r} not in {TIERS}")
        else:
            if tier == "A" and not ("human_meta" in study_type and bias == "sr_assessed"):
                report.error(
                    6,
                    where,
                    "tier A requires human_meta in study_type and bias_assessment "
                    f"'sr_assessed' (study_type={study_type}, bias_assessment={bias!r})",
                )
            if population in POPULATIONS:
                preclinical = population in PRECLINICAL_POPULATIONS
                if (tier == "P") != preclinical:
                    report.error(
                        7,
                        where,
                        f"tier {tier!r} with population {population!r}: tier P is exactly "
                        "the animals and in_vitro rows",
                    )
        if bias not in BIAS_VALUES:
            report.error(6, where, f"bias_assessment {bias!r} not in {BIAS_VALUES}")

        # --- rule 13: the evidence-strength fields carry a stated value ---------
        for field_name, allowed in (
            ("direction", DIRECTIONS),
            ("consistency", CONSISTENCY_VALUES),
            ("independently_replicated", REPLICATION_VALUES),
            ("industry_funded", FUNDING_VALUES),
        ):
            value = claim.get(field_name)
            if value is None:
                report.error(
                    13,
                    where,
                    f"no {field_name}. It is not optional: {allowed} covers every case, "
                    "including not knowing",
                )
            elif value not in allowed:
                report.error(
                    13,
                    where,
                    f"{field_name} {value!r} not in {allowed}; it would drop out of every "
                    f"filter on {field_name}",
                )

        # --- rule 12: counts are null or positive, never 0 ----------------------
        for count_field in ("n_studies", "n_participants"):
            value = claim.get(count_field, None)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                report.error(
                    12,
                    where,
                    f"{count_field} must be null or a positive integer, got {value!r}; "
                    "0 reads as a measured zero",
                )

        # --- shape: free text is single-line strings, sources a list of them ----
        for field_name in (
            "population_detail",
            "effect_size",
            "tier_rationale",
            "dose",
            "duration",
            "delivery_format",
            "safety_flags",
            "notes",
        ):
            _check_text(report, where, field_name, claim.get(field_name))
        sources = claim.get("sources")
        if sources is not None:
            if not isinstance(sources, list):
                # "; ".join over a bare string emits it character-joined -
                # "P; M; I; D; ..." - in the CSV and the readable view.
                report.error(
                    "shape", where, f"sources must be a list of source ids, got {sources!r:.60}"
                )
            else:
                for source in sources:
                    if not isinstance(source, str) or "\n" in source or "\r" in source:
                        report.error(
                            "shape",
                            where,
                            f"sources entries must be single-line strings, got {source!r:.60}",
                        )

        if warnings:
            _claim_warnings(claim, where, report)

    # --- searched_empty: the per-id coverage record ---------------------------------
    # Ids this pass individually searched and could not write a row for. Build and
    # plan derive a deep pass's remaining debt from it (allowed minus claimed minus
    # searched_empty), so a bad entry does more than misdescribe the pass: an id
    # that resolves to nothing hides the search it records, and one that contradicts
    # a claim makes the coverage arithmetic lie.
    searched_raw = shard.data.get("searched_empty")
    if searched_raw is not None and not isinstance(searched_raw, list):
        report.error(
            "shape",
            where_shard,
            f"searched_empty must be a list of impact_ids, got {searched_raw!r:.60}",
        )
        searched_raw = []
    claimed_ids = {
        c.get("impact_id")
        for c in claims_raw
        if isinstance(c, dict) and isinstance(c.get("impact_id"), str)
    }
    seen_searched: set[str] = set()
    for index, entry in enumerate(searched_raw or []):
        if not isinstance(entry, str):
            report.error(
                "shape",
                where_shard,
                f"searched_empty[{index}] must be an impact_id string, got {entry!r:.60}",
            )
            continue
        where = f"{where_shard} searched_empty[{index}]"
        if entry in seen_searched:
            report.error("shape", where, f"{entry} is listed more than once")
        seen_searched.add(entry)
        if entry not in outcomes:
            if entry in excluded_outcomes:
                report.error(
                    "shape",
                    where,
                    f"{entry} is an excluded outcome - out of scope by decision, so "
                    "no search of it was ever owed",
                )
            else:
                report.error(
                    "shape",
                    where,
                    f"{entry} is not in vocabulary/outcomes.json - it records a "
                    "search of nothing, and the debt arithmetic would silently "
                    "ignore it",
                )
            continue
        system = cat.body_system(entry)
        if declared and system not in declared:
            report.error(
                "shape",
                where,
                f"{entry} is a {system} outcome in a shard declaring {declared}; "
                f"the {system} pass's own debt arithmetic will never see it",
            )
        if entry in claimed_ids:
            report.error(
                "shape",
                where,
                f"{entry} is also claimed in this shard - searched-with-no-row next "
                "to that id's row cannot both be true",
            )


def _claim_warnings(claim: dict, where: str, report: Report) -> None:
    """Prose the rules cannot check, reported rather than enforced.

    The line is whether the defect is representable in a finished catalogue. A row
    whose tier nobody justified is thin research and a normal intermediate state; a
    row whose direction is unreadable is broken data, and that is rule 13's job.
    """
    if not str(claim.get("population_detail") or "").strip():
        report.warn(where, "no population_detail - who was studied is unrecorded")
    if not str(claim.get("tier_rationale") or "").strip():
        report.warn(where, "no tier_rationale - the tier is unauditable")
    if not claim.get("sources"):
        report.warn(where, "no sources")
    if (
        claim.get("population") == "humans"
        and claim.get("direction") == "benefit"
        and not str(claim.get("dose") or "").strip()
    ):
        report.warn(where, "human benefit row with no dose is not actionable")

    for key in _unknown_keys(claim, CLAIM_FIELDS):
        report.warn(where, f"unknown claim field {key!r}")


def check_shards(cat: Catalogue, report: Report, only: set[str] | None) -> None:
    roster_ids = set(cat.entity_by_id)
    excluded_ids = set(cat.excluded_by_id)

    for dir_name in cat.entity_dirs:
        if only and dir_name not in only:
            continue
        shards = cat.shards_for(dir_name)

        if dir_name not in roster_ids:
            hint = (
                " - it was dropped to excluded_entities, so its research must be "
                "removed too"
                if dir_name in excluded_ids
                else ""
            )
            report.error(3, f"strains/{dir_name}", f"not a strain_id in roster.json{hint}")

        # Rule 1's scope is the directory, because sharding splits an entity across
        # several files and the dedup guarantee has to hold across all of them.
        seen_claims: dict[tuple, str] = {}
        for shard in shards:
            if shard.strain_id != dir_name:
                report.error(
                    3,
                    shard.rel,
                    f"strain_id {shard.strain_id!r} does not match its directory "
                    f"{dir_name!r}",
                )
            check_shard(cat, shard, report, seen_claims)

    if only:
        for strain_id in sorted(only):
            if strain_id not in roster_ids and strain_id not in excluded_ids:
                report.warn(strain_id, "not a strain_id in roster.json")


def check_template(cat: Catalogue, report: Report) -> None:
    """The template is validated as a shard so it cannot teach an invalid shape.

    Its filename (rule 3) and review date (rule 14) are exempt, along with all
    warnings: it is a skeleton rather than a pass, and its placeholders are loud
    on purpose. Everything about the shape of a claim still applies.
    """
    if cat.template is None:
        # Only actually-missing counts: a template that exists but could not be read
        # is already a parse error, and "missing" would name the wrong fix.
        if not any(rel == "templates/shard.json" for rel, _ in cat.parse_errors):
            report.warn("templates/shard.json", "missing - research passes have no skeleton")
        return
    check_shard(cat, cat.template, report, {}, is_template=True)
    if cat.template.strain_id not in cat.entity_by_id:
        report.error(
            3,
            "templates/shard.json",
            f"example strain_id {cat.template.strain_id!r} is not on the roster",
        )


# --- entry point -----------------------------------------------------------------


def validate(cat: Catalogue, only: set[str] | None = None) -> Report:
    report = Report()
    for rel, message in cat.parse_errors:
        report.error("parse", rel, message)
    if cat.parse_errors and (not cat.roster or not cat.vocabulary):
        # The roster or vocabulary failed to load; every later check would only
        # cascade from that. A roster that is merely empty carries no parse error
        # and falls through to check_roster, which reports what is missing.
        return report
    check_roster(cat, report, only)
    check_vocabulary(cat, report)
    check_triage(cat, report, only)
    check_shards(cat, report, only)
    if not only:
        check_template(cat, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("strain_id", nargs="*", help="limit checks to these entities")
    parser.add_argument("--root", help="catalogue root (default: $CATALOGUE_ROOT or repo)")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on warnings too")
    parser.add_argument("--quiet", action="store_true", help="print only the verdict")
    args = parser.parse_args(argv)

    cat = Catalogue.load(args.root)
    only = set(args.strain_id) or None
    report = validate(cat, only)

    scope = f" ({', '.join(sorted(only))})" if only else ""
    if not args.quiet:
        n_claims = sum(len(s.claims) for s in cat.shards)
        print(
            f"{len(cat.entities)} entities, {len(cat.excluded_entities)} excluded | "
            f"{len(cat.outcomes)} outcomes | {len(cat.entity_dirs)} researched, "
            f"{len(cat.shards)} shards, {n_claims} claims"
        )
        for finding in report.errors:
            print(f"  {finding}")
        for finding in report.warnings:
            print(f"  {finding}")

    if report.errors:
        print(
            f"\nFAIL{scope}: {plural(len(report.errors), 'violation')}, "
            f"{plural(len(report.warnings), 'warning')}"
        )
        return 1
    if args.strict and report.warnings:
        print(
            f"\nFAIL{scope} under --strict: 0 violations, "
            f"{plural(len(report.warnings), 'warning')}"
        )
        return 1
    print(f"\nall 16 validation rules pass{scope}; {plural(len(report.warnings), 'warning')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
