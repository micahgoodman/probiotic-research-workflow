"""Clear papers that PubMed labels as something other than a study.

Rule 2a of RULES.md. A paper is cleared only when PubMed gives it a label from
CLEARS and never gives it a label from KEEPS. Nobody reads a cleared paper, so
the test is deliberately one-sided: when in doubt, keep the paper.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import catalogue as C

# Labels that mean "this paper reports no people of its own".
# A retraction withdraws the paper's results, so it beats every study label below.
RETRACTED = {"Published Erratum": False, "Retraction of Publication": True,
             "Retracted Publication": True}
RETRACTIONS = {k for k, v in RETRACTED.items() if v}

CLEARS = {
    "Review",
    "Systematic Review",
    "Meta-Analysis",
    "Published Erratum",
    "Retraction of Publication",
    "Retracted Publication",
    "Comment",
    "Editorial",
    "Letter",
    "News",
    "Practice Guideline",
    "Guideline",
    "Consensus Development Conference",
    "Bibliography",
    "Biography",
    "Historical Article",
}

# Labels that mean "this paper reports people of its own". These always win.
KEEPS = {
    "Randomized Controlled Trial",
    "Controlled Clinical Trial",
    "Clinical Trial",
    "Clinical Trial, Phase I",
    "Clinical Trial, Phase II",
    "Clinical Trial, Phase III",
    "Clinical Trial, Phase IV",
    "Pragmatic Clinical Trial",
    "Equivalence Trial",
    "Adaptive Clinical Trial",
    "Observational Study",
    "Case Reports",
    "Multicenter Study",
    "Clinical Study",
    "Evaluation Study",
    "Comparative Study",
}

ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def reason(pubtypes):
    """The reason code for a paper the pre-screen clears, or None to keep the paper."""
    types = set(pubtypes)
    if types & RETRACTIONS:
        return "retracted"
    if types & KEEPS:
        return None
    return "not_an_intervention_study" if types & CLEARS else None


def is_not_a_study(pubtypes):
    """True when the pre-screen clears this paper without anyone reading it."""
    return reason(pubtypes) is not None


def record(pmid, pubtypes):
    """The excluded record for a cleared paper."""
    return {"pmid": pmid, "status": "excluded", "excluded_reason": reason(pubtypes)}


def fetch_pubtypes(pmids):
    """Ask PubMed for the publication types of each pmid. Returns {pmid: [type]}."""
    out = {}
    for i in range(0, len(pmids), 200):
        chunk = pmids[i:i + 200]
        url = ESUMMARY + "?" + urllib.parse.urlencode(
            {"db": "pubmed", "id": ",".join(chunk), "retmode": "json"})
        with urllib.request.urlopen(url) as fh:
            data = json.load(fh)
        result = data["result"]
        for pmid in chunk:
            if pmid not in result:
                raise SystemExit(f"PubMed returned nothing for {pmid}")
            out[pmid] = result[pmid].get("pubtype", [])
        time.sleep(2)
    return out


def main():
    cat = C.load()
    found = sorted({p for pmids in cat.search.values() for p in pmids}, key=int)
    todo = [p for p in found if p not in cat.trials]
    print(f"asking PubMed about {len(todo)} papers")
    types = fetch_pubtypes(todo)
    with open(os.path.join(cat.root, "build", "prescreen.json"), "w") as fh:
        json.dump(types, fh, indent=2, sort_keys=True)
    cleared = 0
    for pmid, pubtypes in sorted(types.items(), key=lambda kv: int(kv[0])):
        if is_not_a_study(pubtypes):
            with open(os.path.join(cat.root, "trials", f"{pmid}.json"), "w") as fh:
                json.dump(record(pmid, pubtypes), fh, indent=2)
                fh.write("\n")
            cleared += 1
    print(f"cleared {cleared} of {len(todo)}; {len(todo) - cleared} left to read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
