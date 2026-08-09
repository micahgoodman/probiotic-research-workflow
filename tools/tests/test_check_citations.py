"""The citation check exists because a plausible identifier is not a citation.

The pilot produced four PMIDs that resolved to the wrong paper or to nothing —
caught by hand. validate.py cannot catch this class at all: it is offline and
deterministic on purpose, and a fabricated PMID is perfectly well-formed. So this
tool is the network half of the bargain: every identifier a shard cites must
resolve, and the resolved title is printed next to the claim so a mismatch is
visible to the person reading the output. It never guesses at semantic match -
"resolves, title shown" and "does not resolve" are the only verdicts it issues.
"""

from __future__ import annotations

import contextlib
import io
import json
import unittest

from fixture import CatalogueTestCase

from check_citations import BATCH_SIZE, TransportError, run


def esummary(pmid_titles: dict[str, str]):
    """An esummary JSON body resolving exactly `pmid_titles`."""
    result = {"uids": list(pmid_titles)}
    for pmid, title in pmid_titles.items():
        result[pmid] = {"uid": pmid, "title": title}
    return json.dumps({"result": result})


class FakeFetch:
    """Records every URL fetched and answers from canned responses."""

    def __init__(self, pmid_titles=None, doi_titles=None):
        self.pmid_titles = pmid_titles or {}
        self.doi_titles = doi_titles or {}
        self.urls: list[str] = []

    def __call__(self, url: str, headers: dict) -> str:
        self.urls.append(url)
        if "eutils.ncbi.nlm.nih.gov" in url:
            asked = url.split("id=")[1].split("&")[0].split(",")
            return esummary({p: self.pmid_titles[p] for p in asked if p in self.pmid_titles})
        for doi, title in self.doi_titles.items():
            if url.endswith(doi):
                return json.dumps({"title": title})
        raise TransportError(f"404 for {url}")


FIXTURE_TITLES = {
    "11111111": "Probiotics for antibiotic-associated diarrhea: a meta-analysis",
    "22222222": "Gut barrier effects of strain TS-1 in murine colitis",
    "33333333": "Bacteremia associated with probiotic use: case series",
}


class CheckCitations(CatalogueTestCase):
    def check(self, fetch, only=None):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = run(self.load(), only, fetch)
        return code, buffer.getvalue()

    def test_every_resolved_identifier_prints_its_title(self):
        """The title next to the claim is the whole product: resolution alone only
        proves the id exists, and the wrong-paper failure mode looks exactly like
        the right one until a person reads the title."""
        code, output = self.check(FakeFetch(FIXTURE_TITLES))
        self.assertEqual(0, code)
        for title in FIXTURE_TITLES.values():
            self.assertIn(title, output)
        self.assertIn("gi-aad-prevention", output)

    def test_an_unresolvable_pmid_fails_the_check_and_is_named(self):
        titles = {k: v for k, v in FIXTURE_TITLES.items() if k != "22222222"}
        code, output = self.check(FakeFetch(titles))
        self.assertEqual(1, code)
        self.assertIn("PMID:22222222", output)
        self.assertIn("UNRESOLVED", output)

    def test_a_doi_resolves_through_doi_org(self):
        self.edit_claim(0, sources=["DOI:10.1000/example.42"])
        fetch = FakeFetch(FIXTURE_TITLES, {"10.1000/example.42": "A DOI-resolved study"})
        code, output = self.check(fetch)
        self.assertEqual(0, code)
        self.assertIn("A DOI-resolved study", output)

    def test_an_unrecognized_identifier_scheme_is_unresolved(self):
        """The tool resolves PMIDs and DOIs. Anything else cannot be checked, and
        "could not check" must never pass as "checked"."""
        self.edit_claim(0, sources=["ISBN:978-3-16-148410-0"])
        code, output = self.check(FakeFetch(FIXTURE_TITLES))
        self.assertEqual(1, code)
        self.assertIn("ISBN:978-3-16-148410-0", output)

    def test_proposed_impact_sources_are_checked_too(self):
        """A proposal's evidence lead seeds a future vocabulary row and research
        pass; a fabricated lead poisons both."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update(
                {
                    "proposed_impacts": [
                        {
                            "suggested_label": "x",
                            "suggested_body_system": "GI",
                            "rationale": "y",
                            "sources": ["PMID:99999999"],
                        }
                    ]
                }
            ),
        )
        code, output = self.check(FakeFetch(FIXTURE_TITLES))
        self.assertEqual(1, code)
        self.assertIn("PMID:99999999", output)

    def test_pmids_are_fetched_in_batches(self):
        many = {str(60000000 + i): f"Study number {i}" for i in range(BATCH_SIZE + 50)}
        self.edit_claim(0, sources=[f"PMID:{p}" for p in many])
        fetch = FakeFetch({**FIXTURE_TITLES, **many})
        code, _ = self.check(fetch)
        self.assertEqual(0, code)
        ncbi_calls = [u for u in fetch.urls if "eutils" in u]
        self.assertEqual(2, len(ncbi_calls))

    def test_a_shared_pmid_is_fetched_once_and_reported_per_claim(self):
        self.edit_claim(1, sources=["PMID:11111111"])
        fetch = FakeFetch(FIXTURE_TITLES)
        code, output = self.check(fetch)
        self.assertEqual(0, code)
        asked = ",".join(u.split("id=")[1].split("&")[0] for u in fetch.urls if "eutils" in u)
        self.assertEqual(1, asked.count("11111111"))
        self.assertEqual(2, output.count("11111111"))

    def test_a_transport_failure_is_not_a_verdict(self):
        """Network down must exit differently from "checked and found fabrications":
        one means run it again later, the other means stop and fix the data."""

        def fetch(url, headers):
            raise TransportError("connection refused")

        code, output = self.check(fetch)
        self.assertEqual(2, code)
        self.assertIn("connection refused", output)

    def test_the_strain_filter_limits_the_check(self):
        code, output = self.check(FakeFetch({}), only=["product-test"])
        self.assertEqual(0, code)
        self.assertIn("0 identifiers", output)


if __name__ == "__main__":
    unittest.main()
