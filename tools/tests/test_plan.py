"""The pass plan turns two validation rules into something a pass reads rather than
gets corrected by.

Rule 11 rejects a claim filed outside its body system's shard and rule 2 rejects an
invented impact_id. Both are catchable after the fact; printing the allowed set up
front is what stops a pass writing a shard it will have to redo. If this list were
ever wrong - too wide, or missing an id - it would push passes into exactly the
mistakes the rules exist to catch.
"""

from __future__ import annotations

import contextlib
import io
import os
import unittest

from fixture import CatalogueTestCase, claim

from catalogue import entity_progress, expected_shards
from plan import main, next_to_research, next_to_triage, print_entity, print_status


class ExpectedShards(unittest.TestCase):
    def test_standard_and_light_get_one_pass(self):
        for depth in ("standard", "light"):
            self.assertEqual(["all"], expected_shards({"depth": depth}))

    def test_deep_gets_one_pass_per_outcome_area(self):
        self.assertEqual(
            ["gi", "immune", "mechanistic", "safety"],
            expected_shards({"depth": "deep", "outcome_areas": ["GI", "Immune"]}),
        )

    def test_deep_always_gets_mechanistic_and_safety(self):
        """They cut across every clinical area: gut-barrier work and bacteremia case
        reports surface while researching GI, Immune and Metabolic alike. Giving each a
        single owning pass is what makes a cross-shard duplicate impossible rather than
        merely detectable."""
        self.assertEqual(
            ["mechanistic", "safety"], expected_shards({"depth": "deep", "outcome_areas": []})
        )

    def test_mechanistic_named_in_outcome_areas_is_not_doubled(self):
        self.assertEqual(
            ["gi", "mechanistic", "safety"],
            expected_shards({"depth": "deep", "outcome_areas": ["GI", "Mechanistic", "Safety"]}),
        )

    def test_shards_are_in_canonical_body_system_order(self):
        """So a plan printed twice reads the same way, and coverage lists sort stably."""
        self.assertEqual(
            ["gi", "immune", "metabolic", "mental-health", "mechanistic", "safety"],
            expected_shards(
                {
                    "depth": "deep",
                    "outcome_areas": ["Safety", "Metabolic", "GI", "Mental health", "Immune"],
                }
            ),
        )

    def test_a_dropped_entity_owes_no_passes(self):
        self.assertEqual([], expected_shards({"depth": "drop"}))

    def test_untriaged_is_unknown_not_zero(self):
        """None and [] mean different things: nobody has decided how many passes this
        gets, versus it owes none. Collapsing them would report every untriaged entity
        as complete."""
        self.assertIsNone(expected_shards(None))

    def test_a_depth_nobody_defined_budgets_nothing(self):
        """A depth outside light/standard/deep/drop is a triage entry that decided
        nothing. Guessing a budget for it would commission passes against a plan
        nobody set, so it reads the same as no entry at all."""
        self.assertIsNone(expected_shards({"depth": "extreme"}))
        self.assertIsNone(expected_shards({"depth": 3}))

    def test_a_duplicated_outcome_area_budgets_one_pass(self):
        self.assertEqual(
            ["gi", "mechanistic", "safety"],
            expected_shards({"depth": "deep", "outcome_areas": ["GI", "GI"]}),
        )

    def test_a_non_string_outcome_area_does_not_crash_the_budget(self):
        """Validation warns about it; the budget just skips it. A crash here would
        take plan.py down for every entity because one triage row is malformed."""
        self.assertEqual(
            ["gi", "mechanistic", "safety"],
            expected_shards({"depth": "deep", "outcome_areas": ["GI", ["Immune"]]}),
        )


class Progress(CatalogueTestCase):
    def test_complete_when_every_expected_pass_exists(self):
        self.assertEqual("complete", entity_progress(self.load(), "test-strain").state)

    def test_in_progress_names_what_is_still_owed(self):
        self.deepen(["GI"])
        self.write_shard("gi", ["GI"], [claim()])
        progress = entity_progress(self.load(), "test-strain")
        self.assertEqual("in_progress", progress.state)
        self.assertEqual(["mechanistic", "safety"], progress.missing)

    def test_an_empty_pass_still_counts_as_written(self):
        """"Searched and found nothing" completes the pass. Treating it as outstanding
        would make the entity permanently incomplete and invite someone to search again."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"claims": []}))
        progress = entity_progress(self.load(), "test-strain")
        self.assertEqual("complete", progress.state)
        self.assertEqual(["all"], progress.empty_passes)

    def test_untriaged_entity_is_not_reported_as_started(self):
        self.assertEqual("untriaged", entity_progress(self.load(), "product-test").state)

    def test_an_unreadable_depth_reads_untriaged_not_complete(self):
        """The fixture's all.json is still on disk, but no budget can be stated for a
        depth nobody defined - falling through to the missing=[] arithmetic would
        report an entity whose pass plan nobody can state as finished."""
        self.edit("triage.json", lambda d: d["triage"][0].update({"depth": "extreme"}))
        self.assertEqual("untriaged", entity_progress(self.load(), "test-strain").state)

    def test_deep_entity_with_every_id_accounted_for_is_complete(self):
        """What "done" means for a deep pass: every allowed id ends in a claim row
        or a recorded empty search. Anything looser lets a pass close with ids
        nobody looked at, which is the pilot failure this field exists to surface."""
        self.complete_deep_gi()
        progress = entity_progress(self.load(), "test-strain")
        self.assertEqual("complete", progress.state)
        self.assertEqual([], progress.unfinished)

    def test_a_deep_pass_owing_a_targeted_search_is_unfinished(self):
        """The debt is derived, never declared: forgetting to record a search
        enlarges the visible debt instead of silently claiming coverage."""
        self.complete_deep_gi()
        self.edit("strains/test-strain/gi.json", lambda d: d.update({"searched_empty": []}))
        progress = entity_progress(self.load(), "test-strain")
        self.assertEqual("in_progress", progress.state)
        self.assertEqual(["gi"], progress.unfinished)
        self.assertEqual([], progress.missing)

    def test_adding_a_vocabulary_id_reopens_the_deep_pass_it_lands_in(self):
        """Reconciliation needs no bookkeeping: a new id is allowed, unclaimed and
        unsearched, so the owning pass's derived debt picks it up by arithmetic."""
        self.complete_deep_gi()
        self.edit(
            "vocabulary/outcomes.json",
            lambda d: d["outcomes"].append(
                {"id": "gi-new-outcome", "label": "a newly reconciled outcome", "body_system": "GI"}
            ),
        )
        progress = entity_progress(self.load(), "test-strain")
        self.assertEqual("in_progress", progress.state)
        self.assertEqual(["gi"], progress.unfinished)

    def test_vocabulary_growth_does_not_reopen_a_standard_pass(self):
        """A single all-systems pass owes known-for areas plus a general sweep, not
        a targeted search per id. Unclaimed ids are its normal end state; treating
        them as debt would re-open every light entity forever."""
        self.edit(
            "vocabulary/outcomes.json",
            lambda d: d["outcomes"].append(
                {"id": "gi-new-outcome", "label": "a newly reconciled outcome", "body_system": "GI"}
            ),
        )
        progress = entity_progress(self.load(), "test-strain")
        self.assertEqual("complete", progress.state)
        self.assertEqual([], progress.unfinished)


class NextUp(CatalogueTestCase):
    def test_finishing_beats_starting(self):
        """A catalogue of half-researched entities is worse than a smaller finished one:
        every entity looks present in the readable view while carrying only the body
        systems someone got to first."""

        def mutate(data):
            data["triage"][0].update({"depth": "deep", "outcome_areas": ["GI"]})
            data["triage"].append(
                {
                    "strain_id": "product-test",
                    "n_systematic_reviews": 0,
                    "n_human_trials": 2,
                    "has_preclinical_only_areas": False,
                    "outcome_areas": ["Immune"],
                    "depth": "light",
                    "triage_notes": "Two small trials.",
                }
            )

        self.edit("triage.json", mutate)
        os.remove(self.path("strains/test-strain/all.json"))
        self.write(
            "strains/test-strain/gi.json",
            {
                "strain_id": "test-strain",
                "body_systems": ["GI"],
                "last_reviewed": "2026-08-01",
                "pass_summary": "GI pass.",
                "claims": [],
                "proposed_impacts": [],
                "gaps": "",
            },
        )
        self.assertEqual("test-strain", next_to_research(self.load()))

    def test_next_triage_is_the_first_untriaged_in_roster_order(self):
        """Roster order is the order the sweeps produced, which is what makes a re-run
        a diff rather than a re-derivation."""
        self.assertEqual("product-test", next_to_triage(self.load()))

    def test_nothing_left_returns_none(self):
        self.assertIsNone(next_to_research(self.load()))


class PassPlanOutput(CatalogueTestCase):
    def plan_for(self, strain_id: str) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_entity(self.load(), strain_id)
        return buffer.getvalue()

    def test_lists_exactly_the_impact_ids_the_shard_may_contain(self):
        """Wider than the shard's body system and the plan invites a rule 11 violation;
        narrower and it hides a real outcome from the pass."""
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update({"depth": "deep", "outcome_areas": ["GI"]}),
        )
        os.remove(self.path("strains/test-strain/all.json"))
        output = self.plan_for("test-strain")
        gi_block = output.split("gi.json")[1].split("mechanistic.json")[0]
        self.assertIn("gi-aad-prevention", gi_block)
        self.assertIn("gi-ibs-global", gi_block)
        self.assertNotIn("imm-urti-incidence", gi_block)
        self.assertNotIn("mech-gut-barrier", gi_block)

    def test_excluded_outcomes_are_never_offered(self):
        """They are out of scope by decision. Offering one would reopen a settled
        question inside a research pass instead of in the vocabulary."""
        output = self.plan_for("test-strain")
        self.assertNotIn("skin-acne", output)

    def test_legacy_names_are_shown(self):
        """The 2020 split of Lactobacillus into 25 genera means a search under the
        current name alone misses much of the literature."""
        self.assertIn("Lactobacillus rhamnosus TS-1", self.plan_for("test-strain"))

    def test_untriaged_entity_gets_a_next_step_not_a_guess(self):
        """The pass plan comes from triage depth. Inventing one would commission
        research against a budget nobody set."""
        output = self.plan_for("product-test")
        self.assertIn("NOT TRIAGED", output)

    def test_an_unreadable_depth_gets_a_next_step_not_a_zero_pass_plan(self):
        """Without its own answer this would print "passes (0), 1 written" - a plan
        that looks finished for an entity whose budget nobody can state."""
        self.edit("triage.json", lambda d: d["triage"][0].update({"depth": "extreme"}))
        output = self.plan_for("test-strain")
        self.assertNotIn("passes (0)", output)
        self.assertIn("'extreme'", output)
        self.assertIn("triage.json", output)

    def test_written_passes_are_marked_done(self):
        output = self.plan_for("test-strain")
        self.assertIn("[x] strains/test-strain/all.json", output)
        self.assertIn("3 claims", output)

    def test_a_count_of_one_reads_singular(self):
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update({"claims": [d["claims"][0]]}),
        )
        output = self.plan_for("test-strain")
        self.assertIn("1 claim", output)
        self.assertNotIn("1 claims", output)

    def test_an_excluded_entity_explains_itself(self):
        """Otherwise "not on the roster" reads as a typo when it is actually a decision."""
        output = self.plan_for("product-excluded")
        self.assertIn("excluded_entities", output)
        self.assertIn("criterion 2", output)

    def test_a_drop_entry_without_counts_reads_clean(self):
        """The counts are optional on a drop. "None SRs | None human trials" reads as
        a tool bug, not as an omitted budget."""

        def mutate(data):
            data["triage"][0] = {
                "strain_id": "test-strain",
                "depth": "drop",
                "triage_notes": "Criterion 3.",
            }

        self.edit("triage.json", mutate)
        output = self.plan_for("test-strain")
        self.assertNotIn("None", output)
        self.assertIn("triage: drop", output)

    def test_an_unfinished_pass_lists_only_the_ids_still_owed(self):
        """Re-running research on the entity must land exactly on the remaining
        debt - re-listing already-accounted ids would commission the same search
        twice, and hiding the pass behind [x] would strand the debt forever."""
        self.complete_deep_gi()
        self.edit("strains/test-strain/gi.json", lambda d: d.update({"searched_empty": []}))
        output = self.plan_for("test-strain")
        self.assertIn("[~] strains/test-strain/gi.json", output)
        gi_block = output.split("gi.json")[1].split("mechanistic.json")[0]
        self.assertIn("gi-ibs-global", gi_block)
        self.assertNotIn("gi-aad-prevention", gi_block)

    def test_a_finished_deep_pass_stays_closed(self):
        self.complete_deep_gi()
        output = self.plan_for("test-strain")
        self.assertIn("[x] strains/test-strain/gi.json", output)
        self.assertNotIn("[~]", output)


class SameSpeciesEntities(CatalogueTestCase):
    """Most confusable strains are not exotic: they are other catalogue entities
    under the same species name. Deriving the list from the roster and printing it
    in the pass plan puts the warning at the moment of use, with no second list to
    maintain - the JB-1s of the world stay in triage_notes prose, and the per-study
    identity check covers strains nobody has met yet."""

    def plan_for(self, strain_id: str) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_entity(self.load(), strain_id)
        return buffer.getvalue()

    def add_sibling(self) -> None:
        self.edit(
            "roster.json",
            lambda d: d["entities"].append(
                {
                    "strain_id": "sibling-strain",
                    "entity_type": "single_strain",
                    "preparation": "live",
                    "genus": "Lacticaseibacillus",
                    "species": "rhamnosus",
                    "strain_designation": "XY-9",
                    "also_known_as": [],
                    "known_for": "a sibling placeholder",
                    "roster_source": "fixture",
                }
            ),
        )

    def test_same_species_roster_entities_are_named_in_the_plan(self):
        self.add_sibling()
        output = self.plan_for("test-strain")
        self.assertIn("same species, different entity", output)
        self.assertIn("sibling-strain", output)

    def test_a_dropped_same_species_entity_still_warns(self):
        """An entity stays confusable after it leaves the roster - more so, because
        its studies no longer have any entity to belong to."""
        self.edit(
            "roster.json",
            lambda d: d["excluded_entities"].append(
                {
                    "strain_id": "old-sibling",
                    "label": "Lacticaseibacillus rhamnosus OLD-1",
                    "reason": "fixture: out of scope",
                }
            ),
        )
        output = self.plan_for("test-strain")
        self.assertIn("same species, different entity", output)
        self.assertIn("old-sibling", output)

    def test_an_entity_with_no_siblings_gets_no_block(self):
        self.assertNotIn("same species", self.plan_for("test-strain"))

    def test_a_product_has_no_species_to_match(self):
        """genus/species "multiple" is a placeholder, not a species - matching on it
        would print every product as every other product's confusable."""
        self.add_sibling()
        self.assertNotIn("same species", self.plan_for("product-test"))


class ExitCodes(CatalogueTestCase):
    """0 means the question was answered; 1 means it could not be. A wrapper script
    has to be able to tell "this entity is excluded/untriaged" from "no such id"."""

    def code_for(self, strain_id: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return print_entity(self.load(), strain_id)

    def test_an_excluded_entity_is_an_answer(self):
        self.assertEqual(0, self.code_for("product-excluded"))

    def test_an_untriaged_entity_is_an_answer(self):
        self.assertEqual(0, self.code_for("product-test"))

    def test_an_unreadable_depth_is_an_answer(self):
        self.edit("triage.json", lambda d: d["triage"][0].update({"depth": "extreme"}))
        self.assertEqual(0, self.code_for("test-strain"))

    def test_an_unknown_id_is_not(self):
        self.assertEqual(1, self.code_for("never-heard-of-it"))


class StatusOutput(CatalogueTestCase):
    def test_every_state_is_reported_with_its_count(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_status(self.load())
        output = buffer.getvalue()
        for state, count in (
            ("complete", 1),
            ("in_progress", 0),
            ("not_started", 0),
            ("untriaged", 2),
            ("dropped", 0),
        ):
            self.assertRegex(output, rf"{state}\s+{count}\n")


class Cli(CatalogueTestCase):
    def test_a_corrupt_file_is_reported_not_crashed_on(self):
        with open(self.path("roster.json"), "w", encoding="utf-8") as fh:
            fh.write("[truncated")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["--root", self.root])
        self.assertEqual(1, code)
        self.assertIn("cannot read roster.json", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
