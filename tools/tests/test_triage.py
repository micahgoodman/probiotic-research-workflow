"""triage.py is strict when writing because none of what it refuses is ever normal.

validate.py is tolerant on read - a half-researched catalogue is expected - but a
tool that adds a new defect on purpose has no such excuse. These tests pin the two
mutations that are easy to get wrong by hand: an upsert into a file with no
exclusive owner, and a two-file move that has to leave the strain_id behind.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest

from fixture import CatalogueTestCase

from triage import TriageError, drop, main, record

GOOD = {
    "strain_id": "product-test",
    "n_systematic_reviews": 1,
    "n_human_trials": 4,
    "has_preclinical_only_areas": False,
    "outcome_areas": ["Immune"],
    "depth": "standard",
    "triage_notes": "One SR on URTI incidence; four small RCTs.",
}


class Record(CatalogueTestCase):
    def entries(self) -> list[dict]:
        return self.read("triage.json")["triage"]

    def test_adds_an_entry(self):
        record(self.root, [dict(GOOD)])
        self.assertIn("product-test", [e["strain_id"] for e in self.entries()])

    def test_upserts_rather_than_appending(self):
        """Re-triaging must replace the verdict, not leave two. Two entries for one
        entity make the pass plan depend on which one the reader happens to hit."""
        record(self.root, [dict(GOOD)])
        record(self.root, [{**GOOD, "depth": "light", "triage_notes": "Revised down."}])
        matching = [e for e in self.entries() if e["strain_id"] == "product-test"]
        self.assertEqual(1, len(matching))
        self.assertEqual("light", matching[0]["depth"])

    def test_creates_the_file_when_absent(self):
        """Triage is the first stage to run, so the ordinary case is no file at all."""
        os.remove(self.path("triage.json"))
        record(self.root, [dict(GOOD)])
        data = self.read("triage.json")
        self.assertEqual(1, len(data["triage"]))
        self.assertIn("_comment", data, "the file should explain itself to the next reader")

    def test_accepts_a_batch(self):
        record(self.root, [dict(GOOD), {**GOOD, "strain_id": "species-test"}])
        ids = [e["strain_id"] for e in self.entries()]
        self.assertIn("product-test", ids)
        self.assertIn("species-test", ids)

    def test_refuses_a_batch_naming_one_entity_twice(self):
        """The upsert would keep whichever verdict came last, with no error - the
        same silent last-one-wins that rule 16 exists to keep out of the vocabulary."""
        with self.assertRaises(TriageError) as caught:
            record(self.root, [dict(GOOD), {**GOOD, "depth": "light"}])
        self.assertIn("product-test", str(caught.exception))

    def test_validates_every_entry_before_writing_any(self):
        """A batch that half-applied would leave the caller unable to tell which
        verdicts landed, and re-running would be neither safe nor sufficient."""
        before = self.entries()
        with self.assertRaises(TriageError):
            record(self.root, [dict(GOOD), {**GOOD, "strain_id": "no-such-strain"}])
        self.assertEqual(before, self.entries())

    def test_refuses_an_unknown_strain_id(self):
        """Triage records verdicts about roster entities. Adding an entity is a sweep's
        job, and a sweep records the source that justifies it."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "strain_id": "invented-strain"}])

    def test_refuses_an_unknown_depth(self):
        """depth decides how many passes the entity gets, so an unrecognised value
        makes the pass plan unanswerable rather than wrong."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "depth": "thorough"}])

    def test_refuses_empty_triage_notes(self):
        """A depth call with no reasoning cannot be revisited by anyone who did not
        make it, which is the same failure roster_source exists to prevent."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "triage_notes": "  "}])

    def test_refuses_an_out_of_scope_outcome_area(self):
        """outcome_areas commissions research passes. An excluded system there would
        commission a pass that is required to record nothing."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "outcome_areas": ["Immune", "Skin"]}])

    def test_refuses_a_duplicated_outcome_area(self):
        """Validation only warns about this on read, but the write boundary refuses
        anything it would then have to warn about."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "outcome_areas": ["Immune", "Immune"]}])

    def test_refuses_no_outcome_areas_unless_dropping(self):
        """An entity with no in-scope evidence fails criterion 3. Recording it as
        `standard` with nowhere to look would commission a pass guaranteed to be empty
        and then report the entity as complete."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "outcome_areas": []}])

    def test_refuses_unknown_fields(self):
        """A typo'd field name is silently ignored by every reader, so the value the
        triage pass took the trouble to establish is simply lost."""
        with self.assertRaises(TriageError):
            record(self.root, [{**GOOD, "n_animal_studies": 3}])

    def test_a_drop_needs_only_notes(self):
        """The counts are a budget for research that will not happen."""
        record(
            self.root,
            [
                {
                    "strain_id": "product-test",
                    "depth": "drop",
                    "triage_notes": "Criterion 3: no human trial on an in-scope outcome.",
                }
            ],
        )
        entry = next(e for e in self.entries() if e["strain_id"] == "product-test")
        self.assertEqual("drop", entry["depth"])

    def test_a_drop_entry_with_a_garbage_count_is_refused(self):
        """The counts are optional on a drop, but present-and-wrong is never a normal
        intermediate state - the same field is validated the same at every depth."""
        with self.assertRaises(TriageError):
            record(
                self.root,
                [
                    {
                        "strain_id": "product-test",
                        "depth": "drop",
                        "triage_notes": "Criterion 3.",
                        "n_human_trials": "several",
                    }
                ],
            )

    def test_a_drop_entry_with_an_out_of_scope_area_is_refused(self):
        with self.assertRaises(TriageError):
            record(
                self.root,
                [
                    {
                        "strain_id": "product-test",
                        "depth": "drop",
                        "triage_notes": "Criterion 3.",
                        "outcome_areas": ["Skin"],
                    }
                ],
            )

    def test_a_drop_entry_may_record_empty_outcome_areas(self):
        """No in-scope evidence is exactly what most drops record; an explicit empty
        list is a finding, not an error."""
        record(
            self.root,
            [
                {
                    "strain_id": "product-test",
                    "depth": "drop",
                    "triage_notes": "Criterion 3.",
                    "outcome_areas": [],
                }
            ],
        )
        entry = next(e for e in self.entries() if e["strain_id"] == "product-test")
        self.assertEqual([], entry["outcome_areas"])

    def test_recorded_drop_is_flagged_until_the_move_happens(self):
        """Recording the verdict and moving the entity are two steps on purpose. The
        gap between them has to be visible or it becomes permanent."""
        record(
            self.root,
            [{"strain_id": "product-test", "depth": "drop", "triage_notes": "Criterion 3."}],
        )
        self.assert_warns("still in roster entities")


class Drop(CatalogueTestCase):
    def confirm_drop(self, strain_id: str = "product-test") -> None:
        record(
            self.root,
            [{"strain_id": strain_id, "depth": "drop", "triage_notes": "Criterion 3 fails."}],
        )

    def test_moves_the_entity_and_keeps_its_id(self):
        """A dropped entity that leaves no trace gets re-proposed by the next sweep, and
        one that leaves only a label cannot be matched against the sweep that
        re-proposes it."""
        self.confirm_drop()
        drop(self.root, "product-test", "Criterion 3: no human trial on an in-scope outcome.")
        roster = self.read("roster.json")
        self.assertNotIn("product-test", [e["strain_id"] for e in roster["entities"]])
        excluded = next(e for e in roster["excluded_entities"] if e["strain_id"] == "product-test")
        self.assertEqual("TestBiotic", excluded["label"])
        self.assertIn("Criterion 3", excluded["reason"])

    def test_the_result_still_validates(self):
        """Rule 8 forbids an id in both lists, so a move that copied instead of moving
        would be caught here rather than at the next build."""
        self.confirm_drop()
        drop(self.root, "product-test", "Criterion 3 fails.")
        self.assert_no_errors()

    def test_the_triage_record_survives_the_drop(self):
        """It is the evidence that the drop was confirmed rather than inferred."""
        self.confirm_drop()
        drop(self.root, "product-test", "Criterion 3 fails.")
        self.assertIn("product-test", [e["strain_id"] for e in self.read("triage.json")["triage"]])
        self.assert_no_errors()

    def test_refuses_without_a_confirmed_triage_verdict(self):
        """"A drop is confirmed, never inferred from known_for." Requiring the triage
        record first makes that the tool's behaviour rather than something to remember:
        strains routinely have in-scope evidence their one-line description omits."""
        with self.assertRaises(TriageError) as caught:
            drop(self.root, "product-test", "Looks out of scope.")
        self.assertIn("depth 'drop'", str(caught.exception))
        self.assertIn("product-test", [e["strain_id"] for e in self.read("roster.json")["entities"]])

    def test_refuses_when_triage_said_something_else(self):
        """Guards against dropping the wrong id after triaging a neighbouring one."""
        record(self.root, [dict(GOOD)])
        with self.assertRaises(TriageError):
            drop(self.root, "product-test", "Changed my mind.")

    def test_refuses_an_empty_reason(self):
        """An exclusion nobody can read gets re-argued, which is the whole cost
        excluded_entities exists to avoid."""
        self.confirm_drop()
        with self.assertRaises(TriageError):
            drop(self.root, "product-test", "   ")

    def test_refuses_a_second_drop(self):
        self.confirm_drop()
        drop(self.root, "product-test", "Criterion 3 fails.")
        with self.assertRaises(TriageError):
            drop(self.root, "product-test", "Criterion 3 fails.")

    def test_refuses_an_entity_that_is_not_on_the_roster(self):
        with self.assertRaises(TriageError):
            drop(self.root, "never-existed", "n/a")


class CorruptFiles(CatalogueTestCase):
    """A refusal must name the file that is broken, not misreport the symptom.

    A corrupt roster.json reads as an empty roster, so every entry would be refused
    as "not a strain_id in roster.json"; a corrupt triage.json used to surface as a
    JSON error attributed to the caller's input. Both send the operator to fix the
    wrong thing."""

    def corrupt(self, rel: str) -> None:
        with open(self.path(rel), "w", encoding="utf-8") as fh:
            fh.write("[truncated")

    def test_corrupt_triage_json_is_named(self):
        self.corrupt("triage.json")
        with self.assertRaises(TriageError) as caught:
            record(self.root, [dict(GOOD)])
        self.assertIn("cannot read triage.json", str(caught.exception))

    def test_triage_json_as_a_bare_array_is_named(self):
        self.write("triage.json", [])
        with self.assertRaises(TriageError) as caught:
            record(self.root, [dict(GOOD)])
        self.assertIn("cannot read triage.json", str(caught.exception))

    def test_corrupt_roster_refuses_record(self):
        """Without the upfront check this refuses every entry as "not a strain_id in
        roster.json" - a diagnosis that sends the operator to fix their entries."""
        self.corrupt("roster.json")
        with self.assertRaises(TriageError) as caught:
            record(self.root, [dict(GOOD)])
        self.assertIn("cannot read roster.json", str(caught.exception))

    def test_corrupt_roster_refuses_drop(self):
        self.corrupt("roster.json")
        with self.assertRaises(TriageError) as caught:
            drop(self.root, "product-test", "Criterion 3 fails.")
        self.assertIn("cannot read roster.json", str(caught.exception))


class Cli(CatalogueTestCase):
    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_root_is_accepted_after_the_subcommand(self):
        """`triage.py record --root X` is how every other tool here is invoked;
        rejecting the natural argument order teaches nothing but argparse trivia."""
        code, out, err = self.run_main("record", "--root", self.root, "--json", json.dumps(GOOD))
        self.assertEqual(0, code, err)
        self.assertIn("product-test", out)

    def test_root_before_the_subcommand_still_works(self):
        code, out, err = self.run_main("--root", self.root, "record", "--json", json.dumps(GOOD))
        self.assertEqual(0, code, err)

    def test_interactive_stdin_is_refused_not_waited_on(self):
        """With no --file or --json the tool reads stdin, which at an interactive
        terminal is a silent hang that looks like a crash."""

        class Tty:
            def isatty(self) -> bool:
                return True

        original = sys.stdin
        sys.stdin = Tty()
        try:
            code, out, err = self.run_main("record", "--root", self.root)
        finally:
            sys.stdin = original
        self.assertEqual(1, code)
        self.assertIn("--json", err)

    def test_a_refusal_names_the_problem_and_exits_1(self):
        code, out, err = self.run_main(
            "record", "--root", self.root, "--json", json.dumps({**GOOD, "depth": "thorough"})
        )
        self.assertEqual(1, code)
        self.assertIn("refused", err)
        self.assertIn("thorough", err)


if __name__ == "__main__":
    unittest.main()
