import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from fixture import CONDITIONS, Root, arm, eligible, excluded, found, none_found, not_counted, result, weak  # noqa: E402
import build as B  # noqa: E402
import catalogue as C  # noqa: E402
import search as S  # noqa: E402


class BuildTests(unittest.TestCase):
    def build(self, *trials, **kw):
        root = Root(trials, **kw)
        self.addCleanup(root.cleanup)
        code = B.build(root.path)

        def read(name):
            path = os.path.join(root.path, "build", name)
            if os.path.exists(path):
                with open(path) as f:
                    return f.read()
        return code, read

    def test_the_page_shows_every_tier_with_the_strongest_first(self):
        """A shopper reads from the top. Repeated evidence must come before early signals."""
        code, read = self.build(eligible("1", arms=[arm(("R0175",), results=[weak()])]),
                                eligible("2", arms=[arm(("BB536",))]),
                                eligible("3"), eligible("4"))
        self.assertEqual(code, 0)
        lines = [l for l in read("catalogue.md").splitlines() if l.startswith("| ") and "Tier" not in l]
        self.assertEqual([l.split("|")[1].strip() for l in lines], ["B", "C", "D"])
        self.assertIn("PS128", lines[0])
        self.assertIn("benefit in the one weaker study", lines[2])

    def test_each_study_shows_its_own_size(self):
        """Counting treats a null from 24 people like a null from 400. The reader can only
        tell 'too small to say' from 'well tested' if each study's size is on the page."""
        null = [arm(results=[result(outcome="no_difference")])]
        _, read = self.build(eligible("1", n_randomized=120), eligible("2", arms=null, n_randomized=24),
                             eligible("3", arms=null, n_randomized=None))
        row = [l for l in read("catalogue.md").splitlines() if l.startswith("| B ")][0]
        self.assertIn("benefit (120 people); no difference found (24 people); "
                      "no difference found (size unknown)", row)

    def test_an_unknown_group_size_is_never_shown_as_zero(self):
        """'0 people' reads as a measured zero. When no study reports its size, say so."""
        _, read = self.build(eligible("1", n_randomized=None))
        row = [l for l in read("catalogue.md").splitlines() if l.startswith("| C ")][0]
        self.assertIn("| unknown |", row)
        self.assertNotIn("| 0", row)

    def test_nothing_is_written_when_a_record_is_wrong(self):
        """A catalogue built from bad records looks exactly as trustworthy as a good one."""
        code, read = self.build(eligible("1", n_randomized=-5))
        self.assertEqual(code, 1)
        self.assertIsNone(read("catalogue.md"))

    def test_a_part_done_catalogue_still_builds_and_says_so(self):
        """Between waves of research we must be able to look at the page.

        WHY this matters: the whole point of reading the catalogue between waves is to
        catch a bad rule early. If the page only appeared once all 1,117 papers were read,
        we would find every mistake at the end, which is the version 1 failure again.
        Unread papers are not a defect; a wrong record is, and that still blocks the build.
        """
        code, read = self.build(eligible("1"), search={"felt-stress": ["1", "2", "3"]})
        self.assertEqual(code, 0)
        page = read("catalogue.md")
        self.assertIn("1 of 3", page)
        self.assertIn("2 are still to read", page)
        self.assertIn("still to read", page)

    def test_the_report_counts_trials_that_end_up_counted_no_times(self):
        """This is the catalogue's own blind spot, so it must be on the page, not hidden.

        A follow-up paper is excluded because it is not the first report. When that first
        report is itself excluded (usually because it is paywalled), the trial is in the
        catalogue zero times. A reader who does not see that number would think the search
        was complete. Wave 1 found several.
        """
        _, read = self.build(excluded("1", "not_accessible"),
                             excluded("2", "secondary_report", of_pmid="1"))
        self.assertIn("counted no times", read("screening.md"))
        self.assertIn("2", read("screening.md"))

    def test_the_screening_report_shows_what_was_left_out_and_why(self):
        """The user extends a score list only when the report shows a score is common."""
        t = eligible("2", arms=[arm(results=[not_counted(reason="instrument_not_listed",
                                                         instrument_as_stated="Trier Inventory")])])
        _, read = self.build(eligible("1"), t, excluded("3", "not_oral"))
        report = read("screening.md")
        self.assertIn("not_oral", report)
        self.assertIn("Trier Inventory", report)


class TwoPages(unittest.TestCase):
    """The catalogue is printed in two parts: what a reader can buy today, then the rest.

    WHY this matters: user decision of 18 October 2026. Most readers act by buying
    something, and version 1 over-included strains nobody could buy, so a reader could
    not tell a result they could act on from one they could not. The split is a view over
    the same records with the same rules, so a row appears on exactly one page, and the
    row a reader can act on carries the link and the date it was checked, because pages
    change and nothing more is promised.
    """

    def build(self, available):
        root = Root([eligible("1"), eligible("2", arms=[arm(("R0175",))])],
                    available=available)
        self.addCleanup(root.cleanup)
        self.assertEqual(B.build(root.path), 0)
        with open(os.path.join(root.path, "build", "catalogue.md")) as f:
            return f.read()

    def test_each_row_is_on_exactly_one_page_and_the_buyable_one_carries_the_link(self):
        page = self.build({"ps128": found(), "r0175": none_found()})
        buy, rest = page.split("# Not yet available to buy")
        self.assertIn("# Available to buy today", buy)
        self.assertIn("PS128", buy)
        self.assertNotIn("R0175", buy)
        self.assertIn("R0175", rest)
        self.assertNotIn("PS128", rest)
        self.assertIn("[PS128 capsules](https://shop.example/ps128)", buy)
        self.assertIn("Germany, checked 2026-10-18", buy)

    def test_an_empty_page_says_so_instead_of_vanishing(self):
        """A reader who sees no "available" page would not know whether nothing is for
        sale or the lookups were never done."""
        page = self.build({"ps128": none_found(), "r0175": none_found()})
        buy = page.split("# Not yet available to buy")[0]
        self.assertIn("No entity with a row has a product page on record", buy)


class SearchTests(unittest.TestCase):
    def test_the_query_joins_all_four_parts(self):
        """Without the trial words the search returns reviews; without the human words it
        returns mouse studies. Both would be screened by hand for nothing."""
        q = S.build_query(CONDITIONS["search"], CONDITIONS["conditions"][0])
        self.assertEqual(q, "(probiotic*[tiab]) AND (stress[ti]) AND (randomized[tiab]) "
                            "NOT (animals[mh] NOT humans[mh])")

    def test_a_refresh_never_drops_a_paper(self):
        """PubMed re-indexes papers. If a refresh dropped a PMID, its record would become
        'a paper the search did not find' and the checker would reject finished work."""
        self.assertEqual(S.merge(["1", "2"], ["2", "3"]), ["1", "2", "3"])


if __name__ == "__main__":
    unittest.main()

class NamingLosses(unittest.TestCase):
    """The screening report must name every paper dropped for a naming reason.

    WHY this matters: user ruling of 21 September 2026. Keeping "which strain was this?"
    answerable costs real evidence — 79 papers at the time of the ruling, several of them
    carrying clean between-group results. The user chose to keep the rule and pay that
    price, but a price nobody can see is a price nobody can reconsider. If this list ever
    stops being printed, the cost goes silent and the choice cannot be revisited.
    """

    def test_both_naming_reasons_are_named_paper_by_paper(self):
        root = Root([excluded("1", "not_accessible"),
                     excluded("2", "entity_not_named"),
                     excluded("3", "not_human")],
                    search={"felt-stress": ["1", "2", "3"]})
        try:
            B.build(root.path)
            with open(os.path.join(root.path, "build/screening.md")) as f:
                report = f.read()
        finally:
            root.cleanup()
        self.assertIn("1", report)
        self.assertIn("2", report)
        section = report.split("## Evidence lost because the product was not named")[1]
        self.assertIn("1", section)
        self.assertIn("2", section)
        self.assertNotIn("3", section.split("##")[0])


class ScoreChoiceCost(unittest.TestCase):
    """The screening report names every trial where the choice of score changes the result.

    WHY this matters: in the first full screening the ranking turned a reported benefit
    into a recorded null at least six times, and nobody could see it from a row. A rule
    whose cost is invisible cannot be argued with. Trials whose scores all agree are left
    out, because for them the rule costs nothing.
    """

    def test_only_trials_whose_scores_disagree_are_listed(self):
        split = eligible("1", arms=[arm(results=[
            result("anxiety", "benefit", "stai-state"),
            result("anxiety", "no_difference", "ham-a", main_endpoint="no")])])
        agree = eligible("2", arms=[arm(results=[result("anxiety", "benefit", "stai-state"),
                                                 result("anxiety", "benefit", "ham-a")])])
        root = Root([split, agree], search={"anxiety": ["1", "2"]})
        try:
            self.assertEqual(B.build(root.path), 0)
            with open(os.path.join(root.path, "build/screening.md")) as f:
                report = f.read()
        finally:
            root.cleanup()
        section = report.split("## Trials where the choice of score changes the result")[1].split("##")[0]
        # The main endpoint is flagged because the open question is whether it should win.
        self.assertIn("- 1 anxiety: ham-a no_difference (used); stai-state benefit [main endpoint]",
                      section)
        self.assertNotIn("- 2 ", section)


class SharedRegistrations(unittest.TestCase):
    """The screening report lists every registration number that sits on more than one
    eligible record, with the records.

    WHY this matters: two papers under one number may be one trial reported twice, or two
    honest trials from one registered programme (PS128 in Tourette and in Rett syndrome
    both print NCT03259971). Only a reader of both papers can tell which, so the checker
    no longer refuses them (ruled 18 October 2026); but if the list stopped being printed,
    a double count could sit in the main table with nobody looking. A number on one record
    asks nothing and is left out.
    """

    def test_shared_numbers_are_listed_with_their_records_and_unshared_ones_are_not(self):
        root = Root([eligible("1", registration="NCT00000001"),
                     eligible("2", registration="NCT00000001"),
                     eligible("3", registration="NCT00000002")],
                    search={"felt-stress": ["1", "2", "3"]})
        try:
            self.assertEqual(B.build(root.path), 0)
            with open(os.path.join(root.path, "build/screening.md")) as f:
                report = f.read()
        finally:
            root.cleanup()
        section = report.split("## Registration numbers on more than one eligible record")[1].split("##")[0]
        self.assertIn("- NCT00000001: 1, 2", section)
        self.assertNotIn("NCT00000002", section)


class UnlistedScoreThatNamesAListedOne(unittest.TestCase):
    """An unlisted score whose note names a score that is on a list is marked in the report.

    WHY this matters: on 18 October 2026 a record carried `instrument_not_listed` for
    "Bruni's Sleep Disorders Scale for Children (SDSC)" while `sdsc` sat on the sleep list.
    Such a note is a record to read again, and until it was marked here, finding one took a
    person reading all 152 notes. Only the condition's own list is checked: matching every
    list gave three permanent false marks in the first run and no true one. Whole words
    only: "PSQ" must not match "PSQI".
    """

    def test_a_note_naming_a_score_on_its_own_list_is_marked_and_others_are_not(self):
        own_list = eligible("1", arms=[arm(results=[
            result(), not_counted("anxiety", "instrument_not_listed",
                                  instrument_as_stated="HAM-A, 14 items, clinician-rated")])])
        other_list = eligible("2", arms=[arm(results=[
            result(), not_counted("felt-stress", "instrument_not_listed",
                                  instrument_as_stated="STAI-state, 20 items")])])
        no_list = eligible("3", arms=[arm(results=[
            result(), not_counted("anxiety", "instrument_not_listed",
                                  instrument_as_stated="Visceral Sensitivity Index")])])
        root = Root([own_list, other_list, no_list], search={"felt-stress": ["1", "2", "3"]})
        try:
            self.assertEqual(B.build(root.path), 0)
            with open(os.path.join(root.path, "build/screening.md")) as f:
                report = f.read()
        finally:
            root.cleanup()
        section = report.split("## Scores that are not on a list")[1].split("##")[0]
        self.assertIn("- anxiety: HAM-A, 14 items, clinician-rated (1) [names a listed score: ham-a]", section)
        self.assertIn("- felt-stress: STAI-state, 20 items (1)\n", section)
        self.assertIn("- anxiety: Visceral Sensitivity Index (1)\n", section)
