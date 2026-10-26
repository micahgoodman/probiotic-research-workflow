"""The tier and the verdict are the product. These tests pin what a shopper is told, and why."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from fixture import Root, arm, eligible, result, weak  # noqa: E402
import catalogue as C  # noqa: E402

NULL = [arm(results=[result(outcome="no_difference")])]
WEAK = [arm(results=[weak()])]


def rows(*trials, **kw):
    root = Root(trials, **kw)
    try:
        cat = C.load(root.path)
        assert C.validate(cat) == [], C.validate(cat)
        return C.verdicts(cat)
    finally:
        root.cleanup()


def only(rows_):
    assert len(rows_) == 1, rows_
    return rows_[0]


class TierTests(unittest.TestCase):
    """RULES.md rule 7. The program computes the tier from counted facts, with no exceptions.
    In version 1 a person typed the tier, and every exception needed a ruling and a sweep."""

    def test_two_placebo_trials_are_tier_B(self):
        r = only(rows(eligible("1"), eligible("2")))
        self.assertEqual((r.tier, r.verdict, r.people), ("B", "benefit in all 2 trials", 200))

    def test_one_placebo_trial_is_tier_C(self):
        """64% of version 1's human rows rested on one trial. The reader must see at a
        glance that nobody has repeated the result."""
        r = only(rows(eligible("1")))
        self.assertEqual((r.tier, r.verdict), ("C", "benefit in the one trial"))

    def test_a_change_inside_one_group_is_never_a_trial_win(self):
        """The most common real error in version 1 was reading 'improved from baseline,
        p=0.04' as a win against placebo. It is early evidence and must stay below C."""
        r = only(rows(eligible("1", arms=WEAK)))
        self.assertEqual((r.tier, r.verdict), ("D", "benefit in the one weaker study"))

    def test_weaker_studies_never_lift_a_tier(self):
        """User ruling, 20 September 2026: early evidence is shown, but it cannot stand in
        for a repeat trial. One placebo trial plus three weaker studies is still C."""
        r = only(rows(eligible("1"), eligible("2", arms=WEAK), eligible("3", arms=WEAK),
                      eligible("4", arms=WEAK)))
        self.assertEqual((r.tier, r.trials, r.weaker.benefit), ("C", 1, 3))
        self.assertEqual(r.verdict, "benefit in the one trial")

    def test_a_trial_without_a_placebo_group_is_weaker_evidence(self):
        """Against 'no treatment', people who know they took something report feeling
        better. A difference between such groups is not a placebo-controlled result."""
        for design in ("randomized_other_control", "not_randomized"):
            r = only(rows(eligible("1", design=design), eligible("2", design=design)))
            self.assertEqual((r.tier, r.verdict), ("D", "benefit in all 2 weaker studies"))

    def test_a_tier_D_row_counts_the_people_in_its_own_studies(self):
        r = only(rows(eligible("1", arms=WEAK, n_randomized=30), eligible("2", arms=WEAK, n_randomized=None)))
        self.assertEqual((r.people, r.studies_without_size), (30, 1))

    def test_tier_never_moves_for_size_or_side_endpoints(self):
        """Version 1 docked tiers for small trials, then overturned that ruling the same
        day and re-read 190 rows. Size and endpoint are shown; they never move the tier."""
        small = dict(n_randomized=12, arms=[arm(results=[result(main_endpoint="no")])])
        r = only(rows(eligible("1", **small), eligible("2", **small)))
        self.assertEqual((r.tier, r.people, r.main_endpoint_trials), ("B", 24, 0))


class VerdictTests(unittest.TestCase):
    def test_a_null_trial_is_shown_and_not_hidden(self):
        """A shopper must see that the trials disagree. Version 1 found blended rows that
        kept the positive number and hid the null."""
        r = only(rows(eligible("1"), eligible("2", arms=NULL), eligible("3", arms=NULL)))
        self.assertEqual(r.verdict, "mixed: benefit in 1 of 3 trials")

    def test_a_null_says_found_because_it_is_not_proof_of_no_effect(self):
        """'No difference' reads as 'this does nothing'. Two small trials cannot show that;
        they only failed to find a difference, and the words must say so."""
        r = only(rows(eligible("1", arms=NULL), eligible("2", arms=NULL)))
        self.assertEqual(r.verdict, "no difference found in all 2 trials")
        self.assertEqual(only(rows(eligible("1", arms=NULL))).verdict, "no difference found in the one trial")

    def test_harm_is_never_outvoted(self):
        """One trial that found harm matters more to a shopper than two that found benefit,
        so the verdict must lead with it."""
        r = only(rows(eligible("1"), eligible("2"),
                      eligible("3", arms=[arm(results=[result(outcome="harm")])])))
        self.assertEqual(r.verdict, "harm in 1 of 3 trials")

    def test_main_endpoint_trials_are_counted_for_the_reader(self):
        r = only(rows(eligible("1"), eligible("2", arms=[arm(results=[result(main_endpoint="no")])])))
        self.assertEqual(r.main_endpoint_trials, 1)

    def test_unknown_group_sizes_are_flagged_not_guessed(self):
        r = only(rows(eligible("1"), eligible("2", n_randomized=None)))
        self.assertEqual((r.people, r.studies_without_size), (100, 1))


class EntityTests(unittest.TestCase):
    """RULES.md rule 4: the entity is what the probiotic group took and the control did not."""

    def keys(self, *arms):
        return [C.entity_key(a, {}) for a in arms]

    def test_a_blend_never_feeds_the_single_strain(self):
        """A blend's result belongs to the blend. Version 1 needed a whole rule ('tier rule
        2') and several sweeps because trials of blends leaked into strain pages."""
        a, b = self.keys(arm(("PS128",)), arm(("PS128", "R0175")))
        self.assertNotEqual(a, b)
        r = rows(eligible("1"), eligible("2", arms=[arm(("PS128", "R0175"))]))
        self.assertEqual([x.tier for x in r], ["C", "C"])

    def test_a_co_ingredient_makes_a_different_entity(self):
        """Version 1 asked 'could the vitamin explain the result?' and needed three rulings.
        Version 2 does not ask. The strain plus the vitamin is its own entity."""
        a, b = self.keys(arm(), arm(other_actives=["vitamin B6"]))
        self.assertNotEqual(a, b)

    def test_heat_killed_and_live_never_pool(self):
        a, b = self.keys(arm(), arm(preparation="heat_killed"))
        self.assertNotEqual(a, b)

    def test_spelling_variants_pool(self):
        """'PS 128', 'ps-128' and 'PS128' are one strain. If they did not pool, a strain
        with two trials would look like two tier C strains and never reach tier B."""
        self.assertEqual(len(set(self.keys(arm(("PS 128",)), arm(("ps-128",)), arm(("PS128",))))), 1)

    def test_strain_order_does_not_matter(self):
        a, b = self.keys(arm(("R0052", "R0175")), arm(("R0175", "R0052")))
        self.assertEqual(a, b)

    def test_aliases_join_two_names_for_one_strain(self):
        al = {"yit9029": "shirota"}
        self.assertEqual(C.entity_key(arm(("YIT 9029",)), al), C.entity_key(arm(("Shirota",)), al))

    def test_a_brand_stands_in_when_no_strain_code_is_given(self):
        self.assertEqual(C.entity_key(arm((), brand="Ecologic Barrier"), {}),
                         C.entity_key(arm((), brand="ecologic barrier"), {}))

    def test_an_alias_can_join_a_brand_to_its_strain_list(self):
        al = {"w51+w52": "ecologicbarrier"}
        self.assertEqual(C.entity_key(arm(("W52", "W51")), al),
                         C.entity_key(arm((), brand="Ecologic Barrier"), al))


class ScoreChoice(unittest.TestCase):
    """Rule 5: the record holds every listed score the paper reports; the program picks one.

    WHY this matters: until 21 September 2026 the researcher picked the score while reading
    and threw the other away. PMID 39741947 reported HADS-A (benefit, p = 0.03) and Zung SAS
    (no difference); only the Zung result was saved. That made the ranking rule impossible
    to question: nobody could see what it cost, and changing it meant reading the papers
    again. With both scores in the record, the rule lives in one function, its effect on
    every trial can be computed before anyone rules on it, and adding a score to a list can
    never silently destroy a recorded result.
    """
    BOTH = [arm(results=[result("anxiety", "benefit", "stai-state"),
                         result("anxiety", "no_difference", "ham-a")])]

    def test_the_score_nearer_the_top_of_the_list_gives_the_result(self):
        """HAM-A is rated by a clinician, so it outranks a questionnaire. The order of the
        results inside the record must not matter, or two researchers would disagree."""
        for arms in (self.BOTH, [arm(results=self.BOTH[0]["results"][::-1])]):
            r = only(rows(eligible("1", arms=arms), search={"anxiety": ["1"]}))
            self.assertEqual(r.verdict, "no difference found in the one trial")

    def test_the_list_beats_the_trials_own_primary_endpoint(self):
        """The list wins even when the paper names the other score its primary endpoint.

        WHY this matters: user decision of 21 September 2026, taken with the answer computed
        both ways over all 1,117 papers. Letting a stated primary endpoint jump the list
        would have changed exactly one verdict and reworded six more. The list was kept so
        that every trial is judged on the same score, whether or not its authors named a
        primary endpoint. PMID 40603475 is the case that costs the most: its own primary
        endpoint was a POMS total benefit, and the BDI null outranks it. If someone ever
        makes main_endpoint decide the pick, this test must fail and send them back here.
        """
        arms = [arm(results=[result("anxiety", "benefit", "stai-state", main_endpoint="yes"),
                             result("anxiety", "no_difference", "ham-a", main_endpoint="no")])]
        r = only(rows(eligible("1", arms=arms), search={"anxiety": ["1"]}))
        self.assertEqual(r.verdict, "no difference found in the one trial")

    def test_two_scores_in_one_trial_are_still_one_trial(self):
        """The whole point of tier B is that somebody repeated the result. One trial that
        used two questionnaires has not repeated anything."""
        r = only(rows(eligible("1", arms=self.BOTH), search={"anxiety": ["1"]}))
        self.assertEqual((r.tier, r.trials), ("C", 1))


class ResultsNoSearchAskedFor(unittest.TestCase):
    """A result for a condition whose search never found the paper counts like any other.

    WHY this matters: rule 2's six searches decide which papers get a record, not which
    facts in a record count. On 18 October 2026, 37 of the 39 results recorded for a
    condition the paper was on no list for were counted results; dropping them would have
    changed 31 rows, emptied 25 of them and moved 5 entities from tier B to C. The paper
    reports what it reports, whichever search found it. Ruled 18 October 2026.
    """

    def test_a_result_the_search_did_not_ask_for_still_counts(self):
        arms = [arm(results=[result(), result("anxiety", "benefit", "stai-state")])]
        rows_ = rows(eligible("1", arms=arms))  # the fixture's only search is felt-stress
        self.assertEqual(sorted((r.condition, r.tier) for r in rows_),
                         [("anxiety", "C"), ("felt-stress", "C")])


if __name__ == "__main__":
    unittest.main()
