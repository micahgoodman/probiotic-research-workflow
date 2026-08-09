"""A small, deliberately valid catalogue that each test breaks in exactly one way.

Tests build against this rather than against the real 97-entity roster so that a
failure names a rule rather than a strain, and so that the real data staying valid
is a separate question from the code being correct.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

from catalogue import Catalogue  # noqa: E402
from validate import validate  # noqa: E402

ROSTER = {
    "_version": "test",
    "entities": [
        {
            "strain_id": "test-strain",
            "entity_type": "single_strain",
            "preparation": "live",
            "genus": "Lacticaseibacillus",
            "species": "rhamnosus",
            "strain_designation": "TS-1",
            "also_known_as": ["Lactobacillus rhamnosus TS-1"],
            "known_for": "a placeholder finding",
            "roster_source": "fixture",
        },
        {
            "strain_id": "product-test",
            "entity_type": "product",
            "preparation": "non_viable",
            "genus": "multiple",
            "species": "multiple",
            "strain_designation": "TestBiotic",
            "also_known_as": [],
            "component_strains": ["Lacticaseibacillus rhamnosus TS-1"],
            "known_for": "a placeholder product",
            "roster_source": "fixture",
        },
        {
            "strain_id": "species-test",
            "entity_type": "species_level",
            "preparation": "live",
            "genus": "Streptococcus",
            "species": "thermophilus",
            "strain_designation": "live yogurt cultures",
            "also_known_as": [],
            "known_for": "a placeholder species-level entity",
            "roster_source": "fixture: the evidence base is species-defined",
        },
    ],
    "excluded_entities": [
        {
            "strain_id": "product-excluded",
            "label": "Excluded Product",
            "reason": "fixture: fails criterion 2",
        }
    ],
}

VOCABULARY = {
    "_version": "test",
    "_body_systems": ["GI", "Immune", "Metabolic", "Mental health", "Mechanistic", "Safety"],
    "outcomes": [
        {"id": "gi-aad-prevention", "label": "reduces antibiotic-associated diarrhea", "body_system": "GI"},
        {"id": "gi-ibs-global", "label": "improves overall IBS symptoms", "body_system": "GI"},
        {"id": "imm-urti-incidence", "label": "reduces URTI incidence", "body_system": "Immune"},
        {"id": "met-ldl", "label": "lowers LDL cholesterol", "body_system": "Metabolic"},
        {"id": "mh-sleep", "label": "improves sleep quality", "body_system": "Mental health"},
        {"id": "mech-gut-barrier", "label": "improves gut barrier integrity", "body_system": "Mechanistic"},
        {"id": "safety-bacteremia", "label": "bacteremia or fungemia", "body_system": "Safety"},
    ],
    "excluded_outcomes": [
        {"id": "skin-acne", "label": "improves acne vulgaris", "body_system": "Skin"}
    ],
}

HUMAN_CLAIM = {
    "impact_id": "gi-aad-prevention",
    "direction": "benefit",
    "population": "humans",
    "population_detail": "children receiving antibiotics",
    "study_type": ["human_meta"],
    "evidence_tier": "A",
    "n_studies": 8,
    "n_participants": 1200,
    "independently_replicated": "yes",
    "consistency": "consistent",
    "effect_size": "RR 0.57 [0.41-0.78]",
    "bias_assessment": "sr_assessed",
    "industry_funded": "some",
    "tier_rationale": "SR of 8 RCTs, risk of bias assessed, low heterogeneity.",
    "dose": "1x10^10 CFU/day",
    "duration": "antibiotic course + 1 week",
    "delivery_format": "capsule",
    "safety_flags": "",
    "sources": ["PMID:11111111"],
    "notes": "",
}

ANIMAL_CLAIM = {
    "impact_id": "mech-gut-barrier",
    "direction": "benefit",
    "population": "animals",
    "population_detail": "C57BL/6 mice, DSS colitis",
    "study_type": ["animal"],
    "evidence_tier": "P",
    "n_studies": 3,
    "n_participants": 72,
    "independently_replicated": "unclear",
    "consistency": "consistent",
    "effect_size": "reduced FITC-dextran permeability",
    "bias_assessment": "not_assessed",
    "industry_funded": "unclear",
    "tier_rationale": "Preclinical only.",
    "dose": "1x10^9 CFU/day by gavage",
    "duration": "14 days",
    "delivery_format": "gavage",
    "safety_flags": "",
    "sources": ["PMID:22222222"],
    "notes": "",
}

SAFETY_CLAIM = {
    "impact_id": "safety-bacteremia",
    "direction": "harm",
    "population": "humans",
    "population_detail": "immunocompromised patients with central venous catheters",
    "study_type": ["human_case_report"],
    "evidence_tier": "D",
    "n_studies": 4,
    "n_participants": None,
    "independently_replicated": "yes",
    "consistency": "consistent",
    "effect_size": "",
    "bias_assessment": "not_assessed",
    "industry_funded": "unclear",
    "tier_rationale": "Case reports only; no denominator.",
    "dose": "",
    "duration": "",
    "delivery_format": "",
    "safety_flags": "Avoid in central-line and short-gut patients.",
    "sources": ["PMID:33333333"],
    "notes": "",
}

ALL_SHARD_DATA = {
    "strain_id": "test-strain",
    "body_systems": ["GI", "Immune", "Metabolic", "Mental health", "Mechanistic", "Safety"],
    "last_reviewed": "2026-08-01",
    "pass_summary": "Single pass across all six systems for the fixture entity.",
    "claims": [HUMAN_CLAIM, ANIMAL_CLAIM, SAFETY_CLAIM],
    "proposed_impacts": [],
    "gaps": "",
}

TEMPLATE = {
    "_comment": "fixture template",
    "strain_id": "test-strain",
    "body_systems": ["GI", "Immune", "Metabolic", "Mental health", "Mechanistic", "Safety"],
    "last_reviewed": "YYYY-MM-DD",
    "pass_summary": "What this pass covered.",
    "claims": [HUMAN_CLAIM],
    "proposed_impacts": [],
    "gaps": "",
}

TRIAGE = {
    "_version": "test",
    "triage": [
        {
            "strain_id": "test-strain",
            "n_systematic_reviews": 2,
            "n_human_trials": 12,
            "has_preclinical_only_areas": True,
            "outcome_areas": ["GI", "Immune"],
            "depth": "standard",
            "triage_notes": "fixture",
        }
    ],
}


def claim(base: dict = None, **changes) -> dict:
    """A deep copy of a fixture claim with `changes` applied.

    Deep, not shallow: `dict(HUMAN_CLAIM)` shares its nested `study_type` and
    `sources` lists with the module constant, so one in-place append would poison
    every later test in the process.
    """
    result = copy.deepcopy(base if base is not None else HUMAN_CLAIM)
    result.update(changes)
    return result


class CatalogueTestCase(unittest.TestCase):
    """Writes a valid fixture catalogue to a temp dir; each test mutates one file."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.write("roster.json", copy.deepcopy(ROSTER))
        self.write("vocabulary/outcomes.json", copy.deepcopy(VOCABULARY))
        self.write("templates/shard.json", copy.deepcopy(TEMPLATE))
        self.write("triage.json", copy.deepcopy(TRIAGE))
        self.write("strains/test-strain/all.json", copy.deepcopy(ALL_SHARD_DATA))
        self.addCleanup(self._tmp.cleanup)

    # -- file helpers ---------------------------------------------------------

    def path(self, rel: str) -> str:
        return os.path.join(self.root, rel)

    def write(self, rel: str, data) -> None:
        full = self.path(rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def read(self, rel: str):
        with open(self.path(rel), encoding="utf-8") as fh:
            return json.load(fh)

    def edit(self, rel: str, mutate) -> None:
        """Read, apply `mutate` in place, write back. The single break each test performs.

        `mutate`'s return value is ignored on purpose. An earlier version wrote it back
        when it was not None, which silently replaced the whole file with a string the
        moment a test used `d.pop(...)` - a helper that quietly destroys the fixture is
        worse than no helper, because the test then fails for the wrong reason.
        """
        data = self.read(rel)
        mutate(data)
        self.write(rel, data)

    def edit_claim(self, index: int, **changes) -> None:
        def mutate(data):
            data["claims"][index].update(changes)

        self.edit("strains/test-strain/all.json", mutate)

    def edit_entity(self, strain_id: str, **changes) -> None:
        def mutate(data):
            for entity in data["entities"]:
                if entity["strain_id"] == strain_id:
                    entity.update(changes)

        self.edit("roster.json", mutate)

    # -- deep-entity setup ----------------------------------------------------

    def deepen(self, areas: list[str]) -> None:
        """Re-triage the fixture entity as deep over `areas`, retiring its all.json."""
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update({"depth": "deep", "outcome_areas": areas}),
        )
        os.remove(self.path("strains/test-strain/all.json"))

    def write_shard(self, basename: str, systems: list[str], claims=(), searched_empty=()) -> None:
        self.write(
            f"strains/test-strain/{basename}.json",
            {
                "strain_id": "test-strain",
                "body_systems": systems,
                "last_reviewed": "2026-08-01",
                "pass_summary": f"{basename} pass.",
                "claims": list(claims),
                "proposed_impacts": [],
                "searched_empty": list(searched_empty),
                "gaps": "",
            },
        )

    def complete_deep_gi(self) -> None:
        """A deep GI entity with every allowed id accounted for across its passes:
        each id ends in a claim row or a recorded empty search, which is what "done"
        means for a deep pass."""
        self.deepen(["GI"])
        self.write_shard("gi", ["GI"], [claim(HUMAN_CLAIM)], searched_empty=["gi-ibs-global"])
        self.write_shard("mechanistic", ["Mechanistic"], [claim(ANIMAL_CLAIM)])
        self.write_shard("safety", ["Safety"], [claim(SAFETY_CLAIM)])

    # -- assertions -----------------------------------------------------------

    def load(self) -> Catalogue:
        return Catalogue.load(self.root)

    def validate(self):
        return validate(self.load())

    def assert_rule(self, rule: int, why: str = ""):
        """Assert exactly the named rule fires, and report every finding if not."""
        report = self.validate()
        matched = [f for f in report.errors if f.rule == f"rule {rule}"]
        if not matched:
            self.fail(
                f"rule {rule} did not fire{': ' + why if why else ''}\n"
                + "\n".join(f"  {f}" for f in report.errors + report.warnings)
                + ("\n  (no findings at all)" if not report.errors and not report.warnings else "")
            )
        return matched

    def assert_error(self, label: str, needle: str = ""):
        """Assert a parse- or shape-class error fires (their rule label is the class
        name rather than a number)."""
        report = self.validate()
        matched = [
            f
            for f in report.errors
            if f.rule == label and needle in f"{f.where} {f.message}"
        ]
        if not matched:
            self.fail(
                f"no {label} error containing {needle!r}\n"
                + "\n".join(f"  {f}" for f in report.errors + report.warnings)
                + ("\n  (no findings at all)" if not report.errors and not report.warnings else "")
            )
        return matched

    def assert_no_errors(self):
        report = self.validate()
        if report.errors:
            self.fail("expected no rule violations:\n" + "\n".join(f"  {f}" for f in report.errors))
        return report

    def assert_warns(self, needle: str):
        report = self.validate()
        matched = [f for f in report.warnings if needle in f.message]
        if not matched:
            self.fail(
                f"no warning containing {needle!r}\n"
                + "\n".join(f"  {f}" for f in report.warnings)
            )
        self.assertFalse(
            report.errors,
            "a warning must not also be a rule violation: "
            + "; ".join(str(f) for f in report.errors),
        )
        return matched
