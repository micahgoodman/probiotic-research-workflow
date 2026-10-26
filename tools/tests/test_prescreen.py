"""The pre-screen writes excluded records without anyone reading the paper.

WHY these tests matter: a wrong auto-exclusion is invisible. Nobody reads the
paper again, so the trial is lost from the catalogue for good. Every test here
guards the one thing that keeps that from happening: a paper is only cleared
when PubMed says it is not a study AND never says it is one.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import prescreen as P


class ClearsOnlyNonStudies(unittest.TestCase):
    def test_review_is_cleared(self):
        """A review reports no new people, so it can never hold a trial result."""
        self.assertTrue(P.is_not_a_study(["Review", "Journal Article"]))

    def test_meta_analysis_is_cleared(self):
        """A meta-analysis re-uses other papers' people; its trials are found by our own search."""
        self.assertTrue(P.is_not_a_study(["Meta-Analysis", "Systematic Review"]))

    def test_erratum_and_comment_are_cleared(self):
        """A correction notice and a comment carry no results of their own."""
        self.assertTrue(P.is_not_a_study(["Published Erratum"]))
        self.assertTrue(P.is_not_a_study(["Comment", "Editorial"]))

    def test_plain_journal_article_is_kept(self):
        """Most trials carry no special label at all, so no label must never clear a paper."""
        self.assertFalse(P.is_not_a_study(["Journal Article"]))

    def test_no_labels_at_all_is_kept(self):
        """A record with no publication type is unknown, and unknown is never cleared."""
        self.assertFalse(P.is_not_a_study([]))

    def test_trial_label_beats_review_label(self):
        """PubMed labels some trials 'Review' by mistake; a study label must win, or we lose real trials."""
        self.assertFalse(P.is_not_a_study(["Review", "Randomized Controlled Trial"]))
        self.assertFalse(P.is_not_a_study(["Review", "Clinical Trial"]))
        self.assertFalse(P.is_not_a_study(["Systematic Review", "Observational Study"]))

    def test_unknown_label_never_clears(self):
        """The list of clearing labels is closed, so a new PubMed label cannot silently delete papers."""
        self.assertFalse(P.is_not_a_study(["Some New Label"]))


class Retractions(unittest.TestCase):
    """A retracted paper has been withdrawn by its own authors or journal.

    WHY this matters: the whole catalogue is a claim about what the evidence says. A
    retracted trial's numbers are not evidence, and counting one would put a withdrawn
    result on the page as if it stood. Wave 1 found four retracted papers, and three of
    them also carried a clinical-trial label, so the plain 'a study label always wins'
    rule would have kept every one of them.
    """

    def test_a_retracted_trial_is_cleared_despite_its_trial_label(self):
        self.assertTrue(P.is_not_a_study(["Randomized Controlled Trial", "Retracted Publication"]))
        self.assertTrue(P.is_not_a_study(["Clinical Trial", "Retraction of Publication"]))

    def test_the_reason_says_retracted_not_something_else(self):
        """'not an intervention study' would be a lie about a retracted trial, and the
        screening report is how we learn what the search really returned."""
        self.assertEqual(P.reason(["Randomized Controlled Trial", "Retracted Publication"]),
                         "retracted")
        self.assertEqual(P.reason(["Review"]), "not_an_intervention_study")


class WritesRecordsTheValidatorAccepts(unittest.TestCase):
    def test_record_shape(self):
        """The written record must be the same shape a person would write, or the build breaks."""
        self.assertEqual(
            P.record("12345", ["Review"]),
            {"pmid": "12345", "status": "excluded",
             "excluded_reason": "not_an_intervention_study"},
        )


if __name__ == "__main__":
    unittest.main()
