"""Shared model for the probiotic evidence catalogue.

This module knows where the data lives and how to join it. It is deliberately not
a second source of truth for the data itself: identity lives in roster.json,
outcome labels and body systems live in vocabulary/outcomes.json, and claims live
in shards under strains/. Everything here either locates those files or performs
one of the two joins the build step needs.

The constants below mirror the enumerations in SCHEMA.md. They are duplicated
here because code cannot read prose, and that duplication is the one place this
project accepts drift risk - which is why validate.py checks the roster and the
vocabulary against them rather than trusting either side.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterator

ROOT_ENV = "CATALOGUE_ROOT"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- enumerations from SCHEMA.md -------------------------------------------------

BODY_SYSTEMS = ["GI", "Immune", "Metabolic", "Mental health", "Mechanistic", "Safety"]

# Shard filename per body system. "all" is reserved for a pass that covered all six.
SLUG = {
    "GI": "gi",
    "Immune": "immune",
    "Metabolic": "metabolic",
    "Mental health": "mental-health",
    "Mechanistic": "mechanistic",
    "Safety": "safety",
}
SYSTEM_BY_SLUG = {v: k for k, v in SLUG.items()}
ALL_SHARD = "all"

# Canonical strongest-first order. study_type[0] is the unit a row was graded from,
# which only holds because validation rule 5 forces this order.
STUDY_TYPE_ORDER = [
    "human_meta",
    "human_rct",
    "human_observational",
    "human_case_report",
    "animal",
    "in_vitro",
]
STUDY_TYPE_RANK = {s: i for i, s in enumerate(STUDY_TYPE_ORDER)}

POPULATIONS = ["humans", "animals", "in_vitro"]
PRECLINICAL_POPULATIONS = {"animals", "in_vitro"}
TIERS = ["A", "B", "C", "D", "P"]

ENTITY_TYPES = ["single_strain", "product", "species_level"]
PREPARATIONS = ["live", "non_viable", "mixed"]
DEPTHS = ["deep", "standard", "light", "drop"]

DIRECTIONS = ["benefit", "no effect", "harm"]
CONSISTENCY_VALUES = ["consistent", "mixed", "conflicting"]
REPLICATION_VALUES = ["yes", "no", "unclear"]
BIAS_VALUES = ["sr_assessed", "not_assessed"]
FUNDING_VALUES = ["all", "some", "none", "unclear"]

# --- field sets ------------------------------------------------------------------

ROSTER_FIELDS = [
    "strain_id",
    "entity_type",
    "preparation",
    "genus",
    "species",
    "strain_designation",
    "also_known_as",
    "component_strains",
    "known_for",
    "roster_source",
]
EXCLUSION_FIELDS = ["strain_id", "label", "reason"]

SHARD_FIELDS = [
    "strain_id",
    "body_systems",
    "last_reviewed",
    "pass_summary",
    "claims",
    "proposed_impacts",
    "searched_empty",
    "gaps",
]

CLAIM_FIELDS = [
    "impact_id",
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
    "notes",
]

TRIAGE_FIELDS = [
    "strain_id",
    "n_systematic_reviews",
    "n_human_trials",
    "has_preclinical_only_areas",
    "outcome_areas",
    "depth",
    "triage_notes",
]

# Identity belongs to roster.json alone; copying it into a shard creates the drift
# that sharding would otherwise multiply by the number of passes. See SCHEMA.md
# "Identity - in roster.json only".
IDENTITY_ONLY_FIELDS = [
    "entity_type",
    "preparation",
    "genus",
    "species",
    "strain_designation",
    "also_known_as",
    "component_strains",
    "known_for",
    "roster_source",
]

# The vocabulary is the only home for an outcome's label and body system. A row that
# stores either can disagree with it. See SCHEMA.md "Controlled vocabulary".
OUTCOME_ONLY_FIELDS = ["health_impact", "body_system"]

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_real_date(value: Any) -> bool:
    """A well-formed YYYY-MM-DD naming a date that exists — validation rule 14.

    Both halves are needed: date.fromisoformat alone accepts other layouts
    (YYYYMMDD since Python 3.11), and the regex alone accepts 2026-13-99, which has
    the placeholder's exact failure mode — it sorts after every real date, so the
    oldest-pass rule would skip it and report the entity fresher than it is.
    """
    if not isinstance(value, str) or not ISO_DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


# --- IO --------------------------------------------------------------------------


def resolve_root(root: str | None = None) -> str:
    """Catalogue root: explicit argument, then $CATALOGUE_ROOT, then this checkout."""
    return root or os.environ.get(ROOT_ENV) or PROJECT_ROOT


def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_text(path: str, text: str) -> None:
    """Write via a temp file in the same directory, then rename.

    A partial write would be worse than no write at all: everything written this
    way is read by a later stage or a person, and a truncated file fails in a way
    that looks like missing data rather than like a crash.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def write_json(path: str, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


@contextmanager
def file_lock(path: str) -> Iterator[None]:
    """Exclusive lock guarding a read-modify-write of `path`.

    triage.json is one file that every triage pass appends to, so unlike a shard it
    cannot rely on exclusive ownership to stay safe. Without this, two triage passes
    running at once each read the file, each add their own entries, and the second
    write silently discards the first one's work.
    """
    import fcntl

    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    lock_path = os.path.join(directory, f".{os.path.basename(path)}.lock")
    with open(lock_path, "w", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


# --- shard helpers ---------------------------------------------------------------


def shard_basename(body_systems: list[str]) -> str | None:
    """The filename a pass covering `body_systems` must use, or None if it has none.

    None means the declaration is not expressible as a filename - several systems
    but not all six - which validation rule 3 reports rather than guessing at.
    """
    systems = list(body_systems or [])
    if any(s not in SLUG for s in systems) or len(systems) != len(set(systems)):
        return None
    if set(systems) == set(BODY_SYSTEMS):
        return ALL_SHARD
    if len(systems) == 1:
        return SLUG[systems[0]]
    return None


def systems_for_shard(basename: str) -> list[str]:
    """The body systems a shard filename claims to cover."""
    if basename == ALL_SHARD:
        return list(BODY_SYSTEMS)
    if basename in SYSTEM_BY_SLUG:
        return [SYSTEM_BY_SLUG[basename]]
    return []


def expected_shards(triage_entry: dict | None) -> list[str] | None:
    """Shard basenames a completed research stage must have produced.

    None means unknowable - the entity has not been triaged, so nobody has decided
    how many passes it gets. That is distinct from [] (a dropped entity owes none),
    and coverage.md keeps the two apart.
    """
    if not triage_entry:
        return None
    depth = triage_entry.get("depth")
    if depth == "drop":
        return []
    if depth in ("standard", "light"):
        return [ALL_SHARD]
    if depth != "deep":
        return None
    # isinstance first: membership in SLUG hashes, so an unhashable entry would crash
    # here instead of surfacing as the triage warning it already is. dict.fromkeys:
    # a duplicated outcome area must not budget the pass twice.
    areas = (a for a in (triage_entry.get("outcome_areas") or []) if isinstance(a, str))
    systems = [s for s in dict.fromkeys(areas) if s in SLUG]
    # Mechanistic and Safety always get their own pass: they surface while researching
    # every clinical area, and a single owning pass is what makes a cross-shard
    # duplicate impossible rather than merely detectable.
    for required in ("Mechanistic", "Safety"):
        if required not in systems:
            systems.append(required)
    systems.sort(key=BODY_SYSTEMS.index)
    return [SLUG[s] for s in systems]


@dataclass
class Shard:
    """One research pass, read from strains/<strain_id>/<basename>.json."""

    path: str
    rel: str
    dir_name: str
    basename: str
    data: dict = field(repr=False)

    @property
    def strain_id(self) -> Any:
        return self.data.get("strain_id")

    @property
    def body_systems(self) -> list[str]:
        systems = self.data.get("body_systems")
        return systems if isinstance(systems, list) else []

    @property
    def last_reviewed(self) -> Any:
        return self.data.get("last_reviewed")

    @property
    def pass_summary(self) -> str:
        return self.data.get("pass_summary") or ""

    @property
    def claims(self) -> list[dict]:
        claims = self.data.get("claims")
        return [c for c in claims if isinstance(c, dict)] if isinstance(claims, list) else []

    @property
    def proposed_impacts(self) -> list[dict]:
        proposed = self.data.get("proposed_impacts")
        return [p for p in proposed if isinstance(p, dict)] if isinstance(proposed, list) else []

    @property
    def searched_empty(self) -> list[str]:
        """Ids this pass individually searched and could not write a row for."""
        ids = self.data.get("searched_empty")
        return [i for i in ids if isinstance(i, str)] if isinstance(ids, list) else []

    @property
    def gaps(self) -> str:
        return self.data.get("gaps") or ""


# --- the catalogue ---------------------------------------------------------------


@dataclass
class Catalogue:
    root: str
    roster: dict
    vocabulary: dict
    triage: dict | None
    shards: list[Shard]
    template: Shard | None
    parse_errors: list[tuple[str, str]]

    # -- joins ----------------------------------------------------------------

    @property
    def entities(self) -> list[dict]:
        return [e for e in self.roster.get("entities", []) if isinstance(e, dict)]

    @property
    def excluded_entities(self) -> list[dict]:
        return [e for e in self.roster.get("excluded_entities", []) if isinstance(e, dict)]

    @property
    def entity_by_id(self) -> dict[str, dict]:
        return {e.get("strain_id"): e for e in self.entities if e.get("strain_id")}

    @property
    def excluded_by_id(self) -> dict[str, dict]:
        return {e.get("strain_id"): e for e in self.excluded_entities if e.get("strain_id")}

    @property
    def outcomes(self) -> dict[str, dict]:
        return {
            o.get("id"): o
            for o in self.vocabulary.get("outcomes", [])
            if isinstance(o, dict) and o.get("id")
        }

    @property
    def excluded_outcomes(self) -> dict[str, dict]:
        return {
            o.get("id"): o
            for o in self.vocabulary.get("excluded_outcomes", [])
            if isinstance(o, dict) and o.get("id")
        }

    @property
    def triage_by_id(self) -> dict[str, dict]:
        if not self.triage:
            return {}
        return {
            t.get("strain_id"): t
            for t in self.triage.get("triage", [])
            if isinstance(t, dict) and t.get("strain_id")
        }

    def body_system(self, impact_id: str) -> str | None:
        """The one place a claim's body system comes from. Never stored on the row."""
        outcome = self.outcomes.get(impact_id)
        return outcome.get("body_system") if outcome else None

    def label(self, impact_id: str) -> str | None:
        outcome = self.outcomes.get(impact_id)
        return outcome.get("label") if outcome else None

    def outcomes_in(self, systems: list[str]) -> list[dict]:
        """Vocabulary rows a pass covering `systems` is allowed to use."""
        wanted = set(systems)
        return [o for o in self.outcomes.values() if o.get("body_system") in wanted]

    def shards_for(self, strain_id: str) -> list[Shard]:
        return [s for s in self.shards if s.dir_name == strain_id]

    @property
    def entity_dirs(self) -> list[str]:
        return sorted({s.dir_name for s in self.shards})

    # -- loading --------------------------------------------------------------

    @classmethod
    def load(cls, root: str | None = None) -> "Catalogue":
        root = resolve_root(root)
        parse_errors: list[tuple[str, str]] = []

        def read(rel: str, required: bool) -> dict | None:
            """A JSON object, or None with the reason in parse_errors.

            Wrong-typed counts as unreadable: a truncated or mangled file that still
            parses (as a list, a string) must not be coerced to an empty catalogue -
            that once let the validator pass and the build publish over a destroyed
            roster.
            """
            path = os.path.join(root, rel)
            if not os.path.exists(path):
                if required:
                    parse_errors.append((rel, "file not found"))
                return None
            try:
                data = load_json(path)
            except (json.JSONDecodeError, OSError) as exc:
                parse_errors.append((rel, str(exc)))
                return None
            if not isinstance(data, dict):
                parse_errors.append((rel, f"not a JSON object (got {type(data).__name__})"))
                return None
            return data

        roster = read("roster.json", True) or {}
        vocabulary = read("vocabulary/outcomes.json", True) or {}
        triage = read("triage.json", False)

        shards: list[Shard] = []
        strains_dir = os.path.join(root, "strains")
        if os.path.isdir(strains_dir):
            for dir_name in sorted(os.listdir(strains_dir)):
                entity_dir = os.path.join(strains_dir, dir_name)
                if dir_name.startswith("."):
                    continue
                if not os.path.isdir(entity_dir):
                    # A shard outside an entity directory belongs to no entity. Skipped
                    # silently, a misfiled pass ceases to exist while coverage keeps
                    # reporting it as never run.
                    parse_errors.append(
                        (
                            os.path.relpath(entity_dir, root),
                            "not inside an entity directory - a shard lives at "
                            "strains/<strain_id>/<shard>.json",
                        )
                    )
                    continue
                for filename in sorted(os.listdir(entity_dir)):
                    path = os.path.join(entity_dir, filename)
                    rel = os.path.relpath(path, root)
                    if filename.startswith("."):
                        continue  # lock files, .DS_Store - environment noise, not data
                    if not filename.endswith(".json"):
                        # An editor backup holding the only copy of a pass must not
                        # silently read as the pass never having run.
                        parse_errors.append((rel, "not a <shard>.json file"))
                        continue
                    try:
                        data = load_json(path)
                    except (json.JSONDecodeError, OSError) as exc:
                        parse_errors.append((rel, str(exc)))
                        continue
                    if not isinstance(data, dict):
                        parse_errors.append((rel, "shard is not a JSON object"))
                        continue
                    shards.append(
                        Shard(
                            path=path,
                            rel=rel,
                            dir_name=dir_name,
                            basename=filename[: -len(".json")],
                            data=data,
                        )
                    )

        template = None
        template_rel = "templates/shard.json"
        template_data = read(template_rel, False)
        if template_data is not None:
            template = Shard(
                path=os.path.join(root, template_rel),
                rel=template_rel,
                dir_name="",
                basename="shard",
                data=template_data,
            )

        return cls(
            root=root,
            roster=roster,
            vocabulary=vocabulary,
            triage=triage,
            shards=shards,
            template=template,
            parse_errors=parse_errors,
        )


# --- progress --------------------------------------------------------------------


def unsearched_ids(cat: "Catalogue", shard: Shard) -> list[str]:
    """Allowed ids the pass neither claimed nor recorded as an empty search.

    For a deep pass this is its remaining debt: "done" means a targeted search per
    allowed id, each ending in a claim row or a `searched_empty` entry, and a
    non-empty result re-opens the pass. Derived rather than declared on purpose -
    forgetting to record a search enlarges the visible debt instead of silently
    claiming coverage, and a vocabulary id added after the pass ran lands here by
    arithmetic, so reconciliation re-opens exactly the passes it widens. For a
    standard or light pass the same set is only the sweep's remainder: reported by
    coverage.md, never debt, because that budget owes known-for areas plus a
    general sweep rather than a search per id.
    """
    allowed = {o["id"] for o in cat.outcomes_in(systems_for_shard(shard.basename))}
    accounted = {c.get("impact_id") for c in shard.claims} | set(shard.searched_empty)
    return sorted(allowed - accounted)


@dataclass
class Progress:
    """How far one entity has got, derived from triage depth and shards on disk.

    None of this is an invariant. A half-researched catalogue is the normal state,
    so this feeds coverage.md and the plan tool rather than the validator.
    """

    strain_id: str
    state: str  # untriaged | dropped | not_started | in_progress | complete
    depth: str | None
    expected: list[str] | None  # None: nobody has decided how many passes this gets
    present: list[str]
    missing: list[str]
    unfinished: list[str]  # written deep passes still owing targeted searches
    unexpected: list[str]
    empty_passes: list[str]
    n_claims: int

    @property
    def researched(self) -> bool:
        return bool(self.present)


def entity_progress(cat: "Catalogue", strain_id: str) -> Progress:
    shards = cat.shards_for(strain_id)
    present = sorted(s.basename for s in shards)
    triage_entry = cat.triage_by_id.get(strain_id)
    depth = triage_entry.get("depth") if triage_entry else None
    expected = expected_shards(triage_entry)

    missing = [s for s in (expected or []) if s not in present]
    unexpected = [s for s in present if expected is not None and s not in expected]

    # Only a deep pass owes a targeted search per allowed id, so only a deep pass
    # can be written yet unfinished. A standard or light pass's unclaimed ids are
    # the sweep's normal remainder - treating them as debt would re-open every
    # light entity forever.
    unfinished: list[str] = []
    if depth == "deep":
        by_name = {s.basename: s for s in shards}
        unfinished = [
            basename
            for basename in (expected or [])
            if basename in by_name and unsearched_ids(cat, by_name[basename])
        ]

    if triage_entry is None:
        state = "untriaged"
    elif depth == "drop":
        state = "dropped"
    elif expected is None:
        # A triage entry whose depth does not parse budgets nothing. Falling through
        # would compute missing=[] and read the entity as complete - an entity whose
        # pass plan nobody can state, reported as finished. No usable budget is the
        # untriaged condition, whatever is sitting in the file.
        state = "untriaged"
    elif not present:
        state = "not_started"
    elif missing or unfinished:
        state = "in_progress"
    else:
        state = "complete"

    return Progress(
        strain_id=strain_id,
        state=state,
        depth=depth,
        expected=expected,
        present=present,
        missing=missing,
        unfinished=unfinished,
        unexpected=unexpected,
        empty_passes=sorted(s.basename for s in shards if not s.claims),
        n_claims=sum(len(s.claims) for s in shards),
    )


def all_progress(cat: "Catalogue") -> list[Progress]:
    """Roster order, because that is the order the sweeps produced and it makes a
    re-run a diff."""
    return [entity_progress(cat, e["strain_id"]) for e in cat.entities if e.get("strain_id")]


# --- presentation ----------------------------------------------------------------


def plural(n: int, singular: str, plural_form: str | None = None) -> str:
    """"1 claim", "2 claims" - counts render next to their noun all over the
    compiled views, and "1 claims" reads as a tool that does not look at its own
    output."""
    return f"{n} {singular if n == 1 else (plural_form or singular + 's')}"


def display_name(entity: dict) -> str:
    """Human-facing name. Products and species-level entities have no organism name."""
    genus = entity.get("genus") or ""
    species = entity.get("species") or ""
    designation = entity.get("strain_designation") or ""
    if genus and species and genus != "multiple" and species != "multiple":
        return " ".join(part for part in (genus, species, designation) if part)
    return designation or entity.get("strain_id") or "?"


def oldest_review_date(shards: list[Shard]) -> str | None:
    """An entity's review date is the oldest of its passes, so a partial refresh
    reads stale rather than fresh.

    A plain minimum is correct only because validation rule 14 guarantees every shard
    carries a real ISO date. Without it a placeholder would sort after every real
    date, be skipped by the minimum, and report the entity as fresher than its
    stalest pass - the failure inverted. None only when there are no passes at all.
    """
    dates = [s.last_reviewed for s in shards if isinstance(s.last_reviewed, str)]
    return min(dates) if dates else None
