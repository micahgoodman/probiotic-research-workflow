"""The checker is what lets many researchers work at once without a reviewer reading
every record. Each test names the failure it stops."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from fixture import Root, arm, eligible, excluded, found, none_found, not_counted, result, weak  # noqa: E402
import catalogue as C  # noqa: E402


def errors(*trials, **kw):
    root = Root(trials, **kw)
    try:
        return C.validate(C.load(root.path))
    finally:
        root.cleanup()


class ValidateTests(unittest.TestCase):
    def assertRejected(self, errs, *words):
        self.assertTrue(any(all(w in e for w in words) for e in errs), errs)

    def test_a_clean_catalogue_passes(self):
        self.assertEqual(errors(eligible("1"), excluded("2")), [])

    # --- completeness: this replaces searched_empty, gaps and pass debt from version 1 ---

    def test_every_paper_the_search_found_needs_a_record(self):
        """A skipped paper is invisible. If the checker did not fail here, 'complete' would
        mean 'whatever someone happened to read'."""
        self.assertRejected(errors(eligible("1"), search={"felt-stress": ["1", "2"]}),
                            "2", "no record")

    def test_every_condition_that_found_the_paper_needs_an_answer(self):
        """A paper found by the anxiety search must say what happened to anxiety, even if
        the answer is 'not measured'. A silent skip would hide nulls."""
        self.assertRejected(errors(eligible("1"), search={"felt-stress": ["1"], "anxiety": ["1"]}),
                            "1", "anxiety")

    def test_not_measured_is_an_answer(self):
        t = eligible("1", arms=[arm(results=[result(), not_counted("anxiety", "not_measured")])])
        self.assertEqual(errors(t, search={"felt-stress": ["1"], "anxiety": ["1"]}), [])

    def test_a_paper_the_search_did_not_find_cannot_be_recorded(self):
        """Strain inclusion has no choices in it only while every paper comes from the
        saved searches. A hand-picked paper is a judgment call by another name."""
        self.assertRejected(errors(eligible("1"), eligible("9"), search={"felt-stress": ["1"]}),
                            "9", "not on any saved search list")

    # --- exclusions ---

    def test_an_excluded_paper_needs_a_reason_from_the_fixed_list(self):
        self.assertRejected(errors(excluded("1", reason="too small")), "excluded_reason")

    def test_a_secondary_report_must_name_the_first_report(self):
        """Two papers about one trial must count once, so the later paper points at the
        first one. The pointer is what lets a reader check the trial is in the catalogue."""
        self.assertRejected(errors(excluded("1", "secondary_report")), "of_pmid")
        self.assertEqual(errors(eligible("1"), excluded("2", "secondary_report", of_pmid="1")), [])

    def test_the_first_report_may_be_a_paper_the_searches_never_found(self):
        """This is the common case, and demanding a record for it would stop the work.

        A follow-up paper often reports the mood results of a trial whose first paper was
        about something else entirely, so our six searches never returned it. That first
        paper cannot have a record, because rule 2 refuses any paper not on a search list.
        The pilot of 20 September 2026 hit this on three of thirty papers.
        """
        self.assertEqual(errors(excluded("1", "secondary_report", of_pmid="24249817")), [])

    def test_an_unreadable_first_report_is_not_an_error(self):
        """Nobody can fix this, so it must not stop the build.

        A follow-up paper often points at a first report that is behind a paywall, which
        we record as not_accessible. The trial is then counted no times at all. That is a
        real loss and build/screening.md counts it, but it is a fact about the literature,
        not a mistake in anyone's record. Wave 1 hit it on the first run.
        """
        self.assertEqual(
            errors(excluded("1", "not_accessible"),
                   excluded("2", "secondary_report", of_pmid="1")), [])

    def test_two_papers_sharing_a_registration_number_both_pass(self):
        """A shared registration number is something for a reader to look at, never an error.

        WHY this matters: from 20 September to 18 October 2026 the checker refused any two
        eligible records that shared a number and gave the same thing for the same
        condition. Over 193 registered eligible records it caught no double count (all 54
        secondary reports were marked from the papers' own words) and raised two false
        alarms, one of which kept PMID 42059569, a 240-person trial in men, out of the
        catalogue for 27 days as a "duplicate" of a 112-person trial in women. One trial
        counts once because its later paper says it is a second report (rule 3), not
        because two papers share a number. Shared numbers go to the screening report.
        Ruled 18 October 2026.
        """
        self.assertEqual(errors(eligible("1", registration="NCT00000001"),
                                eligible("2", registration="NCT00000001")), [])

    def test_a_study_without_placebo_is_recorded_and_not_excluded(self):
        """User decision, 20 September 2026: early evidence gets tier D. An exclusion code
        for weak designs would quietly throw that evidence away again."""
        for gone in ("not_randomized", "no_placebo_arm"):
            self.assertRejected(errors(excluded("1", reason=gone)), "excluded_reason")
        self.assertEqual(errors(eligible("1", design="single_group", arms=[arm(results=[weak()])])), [])

    # --- results ---

    def test_a_study_with_one_group_cannot_compare_groups(self):
        """A between-group result is what makes tier B and C. A one-group study that claims
        one is a recording error, and the tier would be wrong in the strong direction."""
        self.assertRejected(errors(eligible("1", design="single_group")), "single_group", "between_groups")

    def test_design_and_comparison_come_from_fixed_lists(self):
        self.assertRejected(errors(eligible("1", design="pilot")), "design")
        self.assertRejected(errors(eligible("1", arms=[arm(results=[result(comparison="vs baseline")])])),
                            "comparison")

    def test_the_score_must_be_on_that_conditions_list(self):
        """PSS is a stress score. Filing it under anxiety would let one measured score
        ground two conditions, which version 1 had to rule against."""
        t = eligible("1", arms=[arm(results=[result(), result("anxiety", instrument="pss")])])
        self.assertRejected(errors(t), "pss", "anxiety")

    def test_an_unlisted_score_must_be_named(self):
        """build/screening.md tallies unlisted scores so the lists can grow on evidence.
        It can only tally what was written down."""
        t = eligible("1", arms=[arm(results=[not_counted(reason="instrument_not_listed")])])
        self.assertRejected(errors(t), "instrument_as_stated")

    def test_a_not_counted_result_needs_a_reason_from_the_fixed_list(self):
        t = eligible("1", arms=[arm(results=[not_counted(reason="seemed weak")])])
        self.assertRejected(errors(t), "reason")

    def test_one_entity_gives_one_result_per_condition_per_trial(self):
        """A trial with a low-dose arm and a high-dose arm is still one trial. Two results
        would let it count twice; rule 4 says record the highest dose only."""
        t = eligible("1", arms=[arm(), arm(dose_as_stated="1 x 10^9 CFU per day")])
        self.assertRejected(errors(t), "twice")

    def test_a_trial_may_record_several_listed_scores_for_one_condition(self):
        """The record holds what the paper reports and the program picks the score (rule 5).
        If the checker refused a second score, researchers would go back to picking one in
        their heads, and the cost of the ranking would be invisible again."""
        t = eligible("1", arms=[arm(results=[result("anxiety", "benefit", "stai-state"),
                                             result("anxiety", "no_difference", "ham-a")])])
        self.assertEqual(errors(t, search={"anxiety": ["1"]}), [])

    def test_the_same_score_cannot_be_recorded_twice(self):
        """One score has one result at the end of treatment. Two would mean the record
        contradicts itself, and the program would have to guess which one is true."""
        t = eligible("1", arms=[arm(results=[result(), result(outcome="no_difference")])])
        self.assertRejected(errors(t), "twice")

    # --- shape ---

    def test_an_arm_must_name_a_strain_or_a_brand(self):
        self.assertRejected(errors(eligible("1", arms=[arm(())])), "strain_codes", "brand")

    def test_unknown_fields_are_rejected(self):
        """Version 1 lost work to near-miss field names ('outcome_id' for 'impact_id').
        An unknown field is a typo until proved otherwise."""
        self.assertRejected(errors(eligible("1", notes="see paper")), "notes")
        self.assertRejected(errors(eligible("1", arms=[arm(results=[result(effect="big")])])), "effect")

    def test_group_size_is_a_positive_number_or_unknown(self):
        self.assertRejected(errors(eligible("1", n_randomized=0)), "n_randomized")
        self.assertEqual(errors(eligible("1", n_randomized=None)), [])

    def test_the_file_name_must_match_the_pmid(self):
        root = Root([eligible("1")])
        try:
            os.rename(os.path.join(root.path, "trials/1.json"), os.path.join(root.path, "trials/x.json"))
            errs = C.validate(C.load(root.path))
        finally:
            root.cleanup()
        self.assertRejected(errs, "x.json")

    def test_a_broken_file_is_an_error_not_a_crash(self):
        root = Root([eligible("1")])
        try:
            with open(os.path.join(root.path, "trials/1.json"), "w") as f:
                f.write("{not json")
            errs = C.validate(C.load(root.path))
        finally:
            root.cleanup()
        self.assertRejected(errs, "1.json")


if __name__ == "__main__":
    unittest.main()


class NotAProbiotic(unittest.TestCase):
    """The searches include synbiotic and postbiotic words, so they return trials of a
    prebiotic fibre, a food or an antibiotic with no bacteria in them at all.

    WHY this matters: filing those as not_an_intervention_study makes the screening report
    say the search returned reviews when it really returned the wrong intervention. The
    report is how we find out whether the search words need changing, so it must be true.
    """

    def test_not_a_probiotic_is_a_reason(self):
        root = Root([{"pmid": "1", "status": "excluded",
                      "excluded_reason": "not_a_probiotic"}])
        try:
            self.assertEqual(C.validate(C.load(root.path)), [])
        finally:
            root.cleanup()


class NamedPapersOnly(unittest.TestCase):
    """A researcher must be able to check their own files.

    WHY this matters: with over a thousand papers still unread, a full check prints a
    thousand 'no record' lines. A researcher cannot find their own mistake in that, so
    they stop checking. Checking named papers only keeps the check usable while the
    work is part-done.
    """

    def check(self, trials, only):
        root = Root(trials, search={"felt-stress": ["1", "2"]})
        try:
            return C.validate(C.load(root.path), only=only)
        finally:
            root.cleanup()

    def test_missing_records_are_not_reported(self):
        """The unread rest of the catalogue is not this researcher's mistake."""
        self.assertEqual(self.check([excluded("1")], only={"1"}), [])

    def test_other_peoples_bad_records_are_not_reported(self):
        """A researcher must not be stopped by a file someone else wrote."""
        bad = {"pmid": "2", "status": "excluded", "excluded_reason": "nonsense"}
        self.assertEqual(self.check([excluded("1"), bad], only={"1"}), [])

    def test_the_named_papers_are_still_fully_checked(self):
        """Narrowing the check must never weaken it, or bad records reach the catalogue."""
        bad = {"pmid": "2", "status": "excluded", "excluded_reason": "nonsense"}
        errs = self.check([excluded("1"), bad], only={"2"})
        self.assertEqual(len(errs), 1, errs)

    def test_full_check_still_demands_every_paper(self):
        """Completeness is the rule the whole catalogue rests on, so it must survive this."""
        root = Root([excluded("1")], search={"felt-stress": ["1", "2"]})
        try:
            errs = C.validate(C.load(root.path))
        finally:
            root.cleanup()
        self.assertTrue(any("2" in e for e in errs), errs)


class PointerChains(unittest.TestCase):
    """A secondary report must point at the trial's own record, not at another
    secondary report.

    WHY this matters: the pointer is what proves the trial is counted somewhere. When it
    lands on another follow-up paper, the trial looks lost even though its record is
    right there, and build/screening.md reports a loss that is not real. Wave 2 of
    21 September 2026 produced exactly this: three PROVIT papers, where 36005642 pointed
    at 32858844, which itself pointed at 33171595. Unlike a paywalled first report, this
    is always fixable by the person writing the record, so it is an error, not a tally.
    """

    def errs(self, *trials):
        root = Root(trials, search={"felt-stress": [t["pmid"] for t in trials]})
        try:
            return C.validate(C.load(root.path))
        finally:
            root.cleanup()

    def test_a_pointer_at_another_secondary_report_is_rejected(self):
        errs = self.errs(eligible("1"),
                         excluded("2", "secondary_report", of_pmid="1"),
                         excluded("3", "secondary_report", of_pmid="2"))
        self.assertTrue(any("3" in e and "2" in e for e in errs), errs)

    def test_pointing_straight_at_the_trial_is_fine(self):
        self.assertEqual(self.errs(eligible("1"),
                                   excluded("2", "secondary_report", of_pmid="1"),
                                   excluded("3", "secondary_report", of_pmid="1")), [])


class OneStrainNamedTwice(unittest.TestCase):
    """An arm may not list one strain twice under two of its names.

    WHY this matters: step 7 of 21 September 2026. PMID 32623402 recorded
    ["A1", "MCC1274"], which are two names for one Bifidobacterium breve strain, and
    PMID 38830472 recorded ["DN-173 010", "CNCM I-2494"] the same way. While aliases.json
    was empty this looked harmless. The moment an alias says those names mean one strain,
    the entity key becomes "mcc1274+mcc1274" and the record silently stops matching the
    real single-strain trials it should pool with. The catalogue must refuse the record
    instead of quietly building a key nobody would ever write on purpose.
    """

    def errs(self, codes, aliases):
        root = Root([eligible("1", arms=[arm(codes)])],
                    search={"felt-stress": ["1"]}, aliases=aliases)
        try:
            return C.validate(C.load(root.path))
        finally:
            root.cleanup()

    def test_two_names_for_one_strain_in_one_arm_are_rejected(self):
        errs = self.errs(("A1", "MCC1274"), {"a1": "mcc1274"})
        self.assertTrue(any("mcc1274" in e and "twice" in e for e in errs), errs)

    def test_two_real_strains_are_still_fine(self):
        self.assertEqual(self.errs(("R0052", "R0175"), {"rosell52": "r0052"}), [])


class TwoArmsOneEntity(unittest.TestCase):
    """One trial may not hold two arms that mean the same entity.

    WHY this matters: user ruling of 21 September 2026, that the vehicle and the coating
    never change the entity. PMID 27178566 tested Duolac Care in two vehicles, and after
    the ruling its two arms became identical twins: same strains, same dose, same key.
    Nothing is built from them today only because both results are unreadable. If either
    result were ever filled in, the program would count one trial as two, which is exactly
    the claim tier B exists to make -- that somebody repeated the result. A ruling that
    merges two arms has to merge them in the record, not leave two copies behind.
    """

    def errs(self, arms):
        root = Root([eligible("1", arms=arms)], search={"felt-stress": ["1"]})
        try:
            return C.validate(C.load(root.path))
        finally:
            root.cleanup()

    def test_two_arms_with_one_entity_key_are_rejected(self):
        """The results are not_counted on purpose: that is the real case.

        A not_counted entry carries no instrument, so the duplicate-instrument check
        cannot see these two arms. Only a check on the entity key itself catches them,
        which is why this test must not use a scored result.
        """
        twin = lambda: arm(("PS128",), results=[not_counted(reason="result_not_accessible")])
        errs = self.errs([twin(), twin()])
        self.assertTrue(any("ps128" in e and "twice" in e for e in errs), errs)

    def test_two_genuinely_different_arms_are_still_fine(self):
        self.assertEqual(self.errs([arm(("PS128",)), arm(("R0175",))]), [])


class AvailabilityIsAnswered(unittest.TestCase):
    """Every entity that gets a row must say whether a reader can buy it (rule 8).

    WHY this matters: user decision of 18 October 2026. The catalogue is printed in two
    parts, what a reader can buy today and the rest, and a row is printed on the second
    page whenever no product page is recorded. So an entity nobody looked up would be
    printed as "not available" with nothing to show for it: the same lie as a paper on a
    search list with no record. "We looked and found nothing" is an answer; silence is a
    gap, and the checker must refuse it. Version 1 kept this test as a judgement inside
    the roster and every change to it forced a reinstatement sweep; here it is one fact
    with no opinion in it, so an entry that carries an opinion is also wrong.
    """

    def errs(self, available, arms=None):
        root = Root([eligible("1", arms=arms)], available=available)
        try:
            return C.validate(C.load(root.path))
        finally:
            root.cleanup()

    def test_an_entity_with_a_row_and_no_entry_is_a_gap(self):
        errs = self.errs({})
        self.assertTrue(any("ps128" in e and "available.json" in e for e in errs), errs)

    def test_none_found_is_an_answer(self):
        self.assertEqual(self.errs({"ps128": none_found()}), [])

    def test_a_found_page_is_an_answer(self):
        self.assertEqual(self.errs({"ps128": found()}), [])

    def test_an_entry_may_not_carry_an_opinion_or_leave_out_the_proof(self):
        """A found page must copy the words that name the entity; a reader checks the
        link, not our say-so. And there is no field for "probably" or "discontinued"."""
        for bad in ({"ps128": found(names="")},
                    {"ps128": found(probably=True)},
                    {"ps128": none_found(url="https://shop.example/x")},
                    {"ps128": {"url": None}}):
            errs = self.errs(bad)
            self.assertTrue(any("ps128" in e for e in errs), (bad, errs))

    def test_an_entity_with_only_not_counted_results_needs_no_entry(self):
        """It gets no row, so there is nothing to print on either page."""
        errs = self.errs({}, arms=[arm(("PS128",), results=[not_counted(reason="result_not_accessible")])])
        self.assertEqual(errs, [])
