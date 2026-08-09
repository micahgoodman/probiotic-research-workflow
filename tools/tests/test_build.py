"""The build step's job is the two joins and refusing to publish invalid data.

The joins are the reason a label lives in exactly one file. These tests change the
single copy and assert the compiled views follow, because that property is what the
whole storage design was bought with - if it ever stopped holding, the schema's
central rule would have become decoration.
"""

from __future__ import annotations

import contextlib
import csv
import io
import os
import unittest

from fixture import ANIMAL_CLAIM, CatalogueTestCase, claim

from build import build, joined_rows, main, render_catalogue_md, render_coverage_md
from catalogue import Catalogue
from validate import validate

TODAY = "2026-08-06"


class BuildTestCase(CatalogueTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.out = os.path.join(self.root, "build")

    def run_build(self):
        return build(self.load(), self.out, today=TODAY)

    def csv_rows(self) -> list[dict]:
        with open(os.path.join(self.out, "catalogue.csv"), encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def read_out(self, name: str) -> str:
        with open(os.path.join(self.out, name), encoding="utf-8") as fh:
            return fh.read()


class Joins(BuildTestCase):
    def test_outcome_label_and_body_system_come_from_the_vocabulary(self):
        """A claim stores impact_id and nothing else about the outcome. If the label
        were copied onto the row, renaming it would mean editing every shard that used
        it, and a missed edit would put one outcome under two names."""
        wrote, _ = self.run_build()
        self.assertTrue(wrote)
        row = next(r for r in self.csv_rows() if r["impact_id"] == "gi-aad-prevention")
        self.assertEqual("reduces antibiotic-associated diarrhea", row["health_impact"])
        self.assertEqual("GI", row["body_system"])

    def test_renaming_a_label_needs_no_shard_edit(self):
        """The property the storage design was bought with, asserted directly."""

        def mutate(data):
            data["outcomes"][0]["label"] = "prevents antibiotic-associated diarrhea"

        self.edit("vocabulary/outcomes.json", mutate)
        self.run_build()
        self.assertIn("prevents antibiotic-associated diarrhea", self.read_out("catalogue.md"))
        row = next(r for r in self.csv_rows() if r["impact_id"] == "gi-aad-prevention")
        self.assertEqual("prevents antibiotic-associated diarrhea", row["health_impact"])

    def test_identity_comes_from_the_roster(self):
        """Same argument on the other axis: a deep entity has several shards, so a
        copied designation would be several copies to keep in step."""
        self.edit_entity("test-strain", strain_designation="TS-1 (ATCC 00000)")
        self.run_build()
        rows = self.csv_rows()
        self.assertTrue(rows)
        self.assertTrue(all(r["strain_designation"] == "TS-1 (ATCC 00000)" for r in rows))

    def test_every_claim_becomes_exactly_one_row(self):
        self.run_build()
        n_claims = sum(len(s.claims) for s in self.load().shards)
        self.assertEqual(n_claims, len(self.csv_rows()))


class ReadableView(BuildTestCase):
    def test_human_and_animal_rows_share_one_impact_heading(self):
        """SCHEMA.md's readable view groups populations under a single impact so two
        evidence bases read as one finding rather than as a duplicate - while the tiers
        stay separate, because preclinical work never raises a human tier."""

        def mutate(data):
            data["claims"].append(
                {
                    **ANIMAL_CLAIM,
                    "impact_id": "gi-aad-prevention",
                    "population_detail": "BALB/c mice",
                }
            )

        self.edit("strains/test-strain/all.json", mutate)
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertEqual(
            1,
            markdown.count("#### reduces antibiotic-associated diarrhea"),
            "one heading, not one per population",
        )
        heading = markdown.split("#### reduces antibiotic-associated diarrhea")[1]
        section = heading.split("####")[0]
        self.assertIn("**humans**", section)
        self.assertIn("**animals**", section)
        self.assertIn("tier **A**", section)
        self.assertIn("tier **P**", section)

    def test_animal_counts_are_not_labelled_participants(self):
        """"96 participants" under a mouse study reads as a clinical trial at a glance,
        which is the exact conflation the humans/animals split exists to prevent."""
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertIn("72 animals", markdown)
        self.assertIn("1,200 participants", markdown)

    def test_empty_fields_are_omitted_not_printed_as_blanks(self):
        """The safety row has no dose, duration or effect size, and this row has no
        population_detail. Printing separators around nothing reads as a measurement
        that came back blank."""
        self.edit_claim(0, population_detail="")
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertNotIn("·  ·", markdown)
        self.assertNotIn(" — \n", markdown)

    def test_a_pass_that_found_nothing_still_appears(self):
        """A shard with claims: [] is a finding: the pass ran and came back empty. If
        the entity vanished from the readable view it would be indistinguishable from
        one nobody has researched."""

        def mutate(data):
            data["claims"] = []
            data["pass_summary"] = "Searched all six systems; nothing met the grading bar."

        self.edit("strains/test-strain/all.json", mutate)
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertIn("nothing met the grading bar", markdown)
        self.assertIn("No gradeable claims recorded", markdown)

    def test_incomplete_entity_is_marked_in_the_readable_view(self):
        """Otherwise a deep entity researched for GI alone reads as a complete picture
        of the strain."""
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update({"depth": "deep", "outcome_areas": ["GI"]}),
        )
        os.remove(self.path("strains/test-strain/all.json"))
        self.write(
            "strains/test-strain/gi.json",
            {
                "strain_id": "test-strain",
                "body_systems": ["GI"],
                "last_reviewed": "2026-08-01",
                "pass_summary": "GI pass.",
                "claims": [claim()],
                "proposed_impacts": [],
                "gaps": "",
            },
        )
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertIn("**Incomplete:**", markdown)
        self.assertIn("mechanistic", markdown)
        self.assertIn("safety", markdown)

    def test_searched_empty_renders_as_a_finding_not_an_absence(self):
        """"Looked and could not write a row" is decision-relevant to a reader: it
        is the difference between absent evidence and an absent search. The label
        joins from the vocabulary like any other outcome reference."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update({"searched_empty": ["gi-ibs-global"]}),
        )
        self.run_build()
        self.assertIn("improves overall IBS symptoms", self.read_out("catalogue.md"))

    def test_an_unfinished_deep_pass_is_marked_in_the_readable_view(self):
        """A deep pass with derived debt is not a complete picture of its body
        system, and the reader has no other way to know."""
        self.complete_deep_gi()
        self.edit("strains/test-strain/gi.json", lambda d: d.update({"searched_empty": []}))
        self.run_build()
        self.assertIn("**Incomplete:**", self.read_out("catalogue.md"))

    def test_review_date_is_the_oldest_pass(self):
        """A partially refreshed entity should read stale rather than fresh."""
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update({"depth": "deep", "outcome_areas": ["GI"]}),
        )
        os.remove(self.path("strains/test-strain/all.json"))
        for basename, systems, day in (
            ("gi", ["GI"], "2024-01-01"),
            ("mechanistic", ["Mechanistic"], "2026-08-01"),
            ("safety", ["Safety"], "2026-08-01"),
        ):
            self.write(
                f"strains/test-strain/{basename}.json",
                {
                    "strain_id": "test-strain",
                    "body_systems": systems,
                    "last_reviewed": day,
                    "pass_summary": f"{basename} pass.",
                    "claims": [],
                    "proposed_impacts": [],
                    "gaps": "",
                },
            )
        self.run_build()
        self.assertIn("Reviewed 2024-01-01 (oldest of 3 passes)", self.read_out("catalogue.md"))

    def test_identity_block_lines_are_hard_breaks(self):
        """Markdown folds adjacent lines into one paragraph unless they end with two
        spaces, so without them the id, aliases and review date render as a run-on
        sentence."""
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertIn("triaged standard  \n", markdown)
        self.assertIn("Lactobacillus rhamnosus TS-1  \n", markdown)

    def test_pass_summaries_render_in_canonical_system_order(self):
        """Directory order is alphabetical, which puts Mechanistic before Metabolic.
        The fixed body-system order is what lets two entities' sections be compared
        line by line."""
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update(
                {"depth": "deep", "outcome_areas": ["Metabolic", "Mental health"]}
            ),
        )
        os.remove(self.path("strains/test-strain/all.json"))
        for basename, system in (
            ("metabolic", "Metabolic"),
            ("mental-health", "Mental health"),
            ("mechanistic", "Mechanistic"),
            ("safety", "Safety"),
        ):
            self.write(
                f"strains/test-strain/{basename}.json",
                {
                    "strain_id": "test-strain",
                    "body_systems": [system],
                    "last_reviewed": "2026-08-01",
                    "pass_summary": f"{system} pass.",
                    "claims": [],
                    "proposed_impacts": [],
                    "gaps": "",
                },
            )
        self.run_build()
        markdown = self.read_out("catalogue.md")
        positions = [
            markdown.index(f"> **{label}.**")
            for label in ("Metabolic", "Mental health", "Mechanistic", "Safety")
        ]
        self.assertEqual(positions, sorted(positions))

    def test_gaps_are_attributed_to_their_pass(self):
        """Two shards' gap notes joined into one sentence read as one blob; the
        reader cannot tell which pass still owes the work."""
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update({"depth": "deep", "outcome_areas": ["GI"]}),
        )
        os.remove(self.path("strains/test-strain/all.json"))
        for basename, system, gaps in (
            ("gi", "GI", "No pediatric RCTs."),
            ("mechanistic", "Mechanistic", ""),
            ("safety", "Safety", "No search of case reports after 2020."),
        ):
            self.write(
                f"strains/test-strain/{basename}.json",
                {
                    "strain_id": "test-strain",
                    "body_systems": [system],
                    "last_reviewed": "2026-08-01",
                    "pass_summary": f"{system} pass.",
                    "claims": [],
                    "proposed_impacts": [],
                    "gaps": gaps,
                },
            )
        self.run_build()
        markdown = self.read_out("catalogue.md")
        self.assertIn("GI: No pediatric RCTs.", markdown)
        self.assertIn("Safety: No search of case reports after 2020.", markdown)

    def test_a_placeholder_date_never_reaches_the_readable_view(self):
        """Rule 14 is what lets the oldest-pass calculation be a plain minimum. Without
        it "YYYY-MM-DD" sorts after every real date, gets skipped, and reports the
        entity as fresher than its stalest pass. The build refuses rather than
        rendering around it, so no fallback is carried for a state that cannot occur."""
        self.edit(
            "strains/test-strain/all.json", lambda d: d.update({"last_reviewed": "YYYY-MM-DD"})
        )
        wrote, messages = self.run_build()
        self.assertFalse(wrote)
        self.assertTrue(any("rule 14" in m for m in messages))


class RefusesToPublishInvalidData(BuildTestCase):
    def test_validation_failure_blocks_the_build(self):
        """The compiled views are the surface people read. Publishing from data already
        known to be invalid is the one way a defect becomes invisible."""
        self.edit_claim(0, impact_id="gi-invented-outcome")
        wrote, messages = self.run_build()
        self.assertFalse(wrote)
        self.assertTrue(any("rule 2" in m for m in messages))

    def test_nothing_is_written_when_the_build_refuses(self):
        """A refusal that still wrote catalogue.csv would leave a valid-looking file
        next to an error message nobody re-reads."""
        self.run_build()
        before = self.read_out("catalogue.csv")
        self.edit_claim(0, evidence_tier="A", study_type=["human_rct"])
        wrote, _ = self.run_build()
        self.assertFalse(wrote)
        self.assertEqual(before, self.read_out("catalogue.csv"), "stale output was overwritten")

    def test_warnings_do_not_block_the_build(self):
        """Warnings describe an incomplete catalogue, which is normal. If they blocked
        a build, the only way to see coverage.md would be to fix the incompleteness
        coverage.md exists to report."""
        self.edit_claim(0, population_detail="")
        wrote, _ = self.run_build()
        self.assertTrue(wrote)
        self.assertIn("population_detail", self.read_out("coverage.md"))


class Coverage(BuildTestCase):
    def test_states_are_counted(self):
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("| complete | 1 |", coverage)
        self.assertIn("| untriaged | 2 |", coverage)

    def test_untriaged_entities_are_listed_by_name(self):
        """"Is the catalogue done?" has to be answerable without opening 97 directories."""
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("`product-test`", coverage)
        self.assertIn("`species-test`", coverage)

    def test_missing_passes_are_named(self):
        self.edit(
            "triage.json",
            lambda d: d["triage"][0].update({"depth": "deep", "outcome_areas": ["GI", "Immune"]}),
        )
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
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("**missing: immune, mechanistic, safety**", coverage)

    def test_empty_passes_are_reported_separately_from_missing_ones(self):
        """"Searched and found nothing" and "not searched" are different answers, and
        the whole reason a pass always writes its shard is to keep them apart."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"claims": []}))
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("Passes that ran and found nothing", coverage)
        self.assertIn("`test-strain/all.json`", coverage)

    def test_proposed_impacts_are_collected_for_reconciliation(self):
        """A proposal buried in one shard of one entity is a proposal nobody acts on."""

        def mutate(data):
            data["proposed_impacts"] = [
                {
                    "suggested_label": "reduces post-infectious IBS onset",
                    "suggested_body_system": "GI",
                    "rationale": "No existing id covers onset rather than symptoms.",
                    "sources": ["PMID:44444444"],
                }
            ]

        self.edit("strains/test-strain/all.json", mutate)
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("Proposed impacts awaiting reconciliation", coverage)
        self.assertIn("reduces post-infectious IBS onset", coverage)

    def test_shards_no_longer_expected_are_surfaced_and_counted_as_shards(self):
        """Re-triaging an entity from deep to standard leaves orphan shards whose claims
        are still valid. Silence here would let the pass plan and the data disagree -
        and the heading counts shards, because "(1)" over a line naming two files
        reads as a miscount."""
        for basename, system in (("gi", "GI"), ("immune", "Immune")):
            self.write(
                f"strains/test-strain/{basename}.json",
                {
                    "strain_id": "test-strain",
                    "body_systems": [system],
                    "last_reviewed": "2026-08-01",
                    "pass_summary": "Left over from a deeper budget.",
                    "claims": [],
                    "proposed_impacts": [],
                    "gaps": "",
                },
            )
        self.run_build()
        self.assertIn("Shards present but not expected (2)", self.read_out("coverage.md"))

    def test_searched_empty_ids_are_reported_per_shard(self):
        """"Searched, could not write a row" is the id-level version of the empty
        pass: without it, an absent row is indistinguishable from an absent search."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update({"searched_empty": ["gi-ibs-global"]}),
        )
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("`test-strain/all.json`", coverage)
        self.assertIn("gi-ibs-global", coverage)

    def test_a_deep_passs_derived_debt_is_listed_with_its_ids(self):
        """The debt is the re-open signal: coverage.md is where an operator sees
        that a "written" deep pass still owes targeted searches, and which ones."""
        self.complete_deep_gi()
        self.edit("strains/test-strain/gi.json", lambda d: d.update({"searched_empty": []}))
        self.run_build()
        coverage = self.read_out("coverage.md")
        self.assertIn("`test-strain/gi.json`", coverage)
        self.assertIn("gi-ibs-global", coverage)
        self.assertIn("unfinished: gi", coverage)

    def test_a_swept_remainder_is_counted_not_enumerated(self):
        """A standard or light pass legitimately leaves most of the vocabulary to
        the general sweep; enumerating ~55 ids per light entity would bury the
        actionable sections under boilerplate."""
        self.run_build()
        self.assertIn("4 of 7", self.read_out("coverage.md"))

    def test_counts_of_one_read_singular(self):
        self.edit("strains/test-strain/all.json", lambda d: d.update({"claims": [claim()]}))
        wrote, messages = self.run_build()
        self.assertTrue(wrote)
        self.assertIn("1 claim from 1 shard across 1 entity", messages[0])
        coverage = self.read_out("coverage.md")
        self.assertIn("1 pass, 1 claim", coverage)
        self.assertNotIn("1 claims", coverage)


class StableOutput(BuildTestCase):
    def test_row_order_does_not_depend_on_claim_order_in_the_shard(self):
        """A rebuild diff should show real changes, not reshuffling."""
        self.run_build()
        before = [r["impact_id"] for r in self.csv_rows()]
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update({"claims": list(reversed(d["claims"]))}),
        )
        self.run_build()
        self.assertEqual(before, [r["impact_id"] for r in self.csv_rows()])

    def test_rows_are_ordered_by_body_system_then_vocabulary(self):
        """Vocabulary order, not alphabetical: the vocabulary groups related outcomes,
        and alphabetising would scatter them. The file order is made non-alphabetical
        here so a sort that only looks alphabetical cannot pass."""
        self.edit(
            "vocabulary/outcomes.json",
            lambda d: d["outcomes"].sort(key=lambda o: o["id"] != "gi-ibs-global"),
        )
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d["claims"].extend(
                [
                    claim(impact_id="mh-sleep"),
                    claim(impact_id="met-ldl"),
                    claim(impact_id="gi-ibs-global"),
                ]
            ),
        )
        self.run_build()
        self.assertEqual(
            [
                "gi-ibs-global",
                "gi-aad-prevention",
                "met-ldl",
                "mh-sleep",
                "mech-gut-barrier",
                "safety-bacteremia",
            ],
            [r["impact_id"] for r in self.csv_rows()],
        )

    def test_within_an_impact_humans_sort_before_animals(self):
        """The human row is the one a reader acts on; the animal row is context, and
        file order in the shard must not decide which comes first."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d["claims"].insert(
                0, claim(ANIMAL_CLAIM, impact_id="gi-aad-prevention")
            ),
        )
        self.run_build()
        rows = [r for r in self.csv_rows() if r["impact_id"] == "gi-aad-prevention"]
        self.assertEqual(["humans", "animals"], [r["population"] for r in rows])


class EmptyCatalogue(BuildTestCase):
    def test_builds_before_any_research_exists(self):
        """The first thing anyone runs. It must produce a real coverage report rather
        than an empty file or a crash."""
        import shutil

        shutil.rmtree(self.path("strains"))
        wrote, _ = self.run_build()
        self.assertTrue(wrote)
        self.assertIn("Nothing researched yet", self.read_out("catalogue.md"))
        self.assertIn("| untriaged | 2 |", self.read_out("coverage.md"))
        self.assertEqual([], self.csv_rows())


class AtomicOutput(BuildTestCase):
    def test_output_directory_holds_only_the_three_views(self):
        """The writes go through a temp file and a rename so a crash mid-write cannot
        leave a truncated catalogue behind; success must not leave the temp files
        behind either."""
        self.run_build()
        self.assertEqual(
            ["catalogue.csv", "catalogue.md", "coverage.md"], sorted(os.listdir(self.out))
        )


class Cli(BuildTestCase):
    def run_main(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--root", self.root, "--out", self.out])
        return code, out.getvalue()

    def test_a_refusal_warns_that_previous_output_is_stale(self):
        """The refusal protects readers of build/ - but only if they hear about it.
        Files from before the breakage look current to anyone who opens them."""
        self.run_build()
        self.edit_claim(0, impact_id="gi-invented-outcome")
        code, out = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("stale", out)

    def test_a_refusal_with_no_previous_build_reports_nothing_written(self):
        self.edit_claim(0, impact_id="gi-invented-outcome")
        code, out = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("Nothing written", out)
        self.assertNotIn("stale", out)


class RenderersAreSideEffectFree(BuildTestCase):
    def test_renderers_do_not_need_an_output_directory(self):
        """Both renderers are pure so a test - or a reviewer - can look at the output
        without writing to the repo."""
        cat = self.load()
        rows = joined_rows(cat)
        report = validate(cat)
        self.assertIn("# Probiotic Evidence Catalogue", render_catalogue_md(cat, rows, TODAY))
        self.assertIn("# Coverage report", render_coverage_md(cat, report.warnings, TODAY))
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
