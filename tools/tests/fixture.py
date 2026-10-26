"""A tiny catalogue on disk for the tests. Two conditions are enough to test every rule."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from catalogue import entity_key  # noqa: E402

CONDITIONS = {
    "search": {
        "probiotic_terms": "(probiotic*[tiab])",
        "study_terms": "(randomized[tiab])",
        "human_terms": "NOT (animals[mh] NOT humans[mh])",
    },
    "conditions": [
        {"id": "felt-stress", "label": "Felt stress", "benefit_means": "a lower score",
         "pubmed_terms": "(stress[ti])",
         "instruments": [{"id": "pss", "label": "PSS total", "aliases": ["PSS"]}]},
        {"id": "anxiety", "label": "Anxiety", "benefit_means": "a lower score",
         "pubmed_terms": "(anxiety[tiab])",
         "instruments": [{"id": "ham-a", "label": "HAM-A total", "aliases": []},
                         {"id": "stai-state", "label": "STAI state", "aliases": []}]},
    ],
}


def result(condition="felt-stress", outcome="benefit", instrument="pss", **over):
    r = {"condition": condition, "result": outcome, "instrument": instrument,
         "comparison": "between_groups", "main_endpoint": "yes"}
    r.update(over)
    return r


def not_counted(condition="felt-stress", reason="not_measured", **over):
    r = {"condition": condition, "result": "not_counted", "reason": reason}
    r.update(over)
    return r


def arm(codes=("PS128",), results=None, **over):
    a = {"entity_as_stated": "L. plantarum " + " ".join(codes), "strain_codes": list(codes),
         "brand": None, "other_actives": [], "preparation": "live",
         "dose_as_stated": "1 x 10^10 CFU per day", "weeks": 8,
         "results": [result()] if results is None else results}
    a.update(over)
    return a


def weak(outcome="benefit", **over):
    """A result from inside one group: 'improved from the start', with no placebo comparison."""
    return result(outcome=outcome, comparison="within_group", **over)


def found(url="https://shop.example/ps128", product="PS128 capsules", country="Germany", **over):
    """Rule 8: one consumer product page that names the entity and lets a person buy it."""
    e = {"url": url, "product": product, "country": country, "checked": "2026-10-18",
         "names": "Lactobacillus plantarum PS128"}
    e.update(over)
    return e


def none_found(**over):
    e = {"url": None, "checked": "2026-10-18", "searched": "no consumer product names this code"}
    e.update(over)
    return e


def eligible(pmid, arms=None, **over):
    t = {"pmid": pmid, "status": "eligible", "design": "randomized_placebo",
         "registration": None, "n_randomized": 100,
         "population": "healthy adults", "arms": [arm()] if arms is None else arms}
    t.update(over)
    return t


def excluded(pmid, reason="not_human", **over):
    t = {"pmid": pmid, "status": "excluded", "excluded_reason": reason}
    t.update(over)
    return t


class Root:
    """Writes a catalogue into a temp folder. search maps condition id -> list of pmids."""

    def __init__(self, trials=(), search=None, aliases=None, conditions=None, available=None):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = self._tmp.name
        for d in ("search", "trials", "build"):
            os.mkdir(os.path.join(self.path, d))
        self.write("conditions.json", conditions or CONDITIONS)
        self.write("aliases.json", {"aliases": aliases or {}})
        trials = list(trials)
        if available is None:  # by default nothing was found for sale: rule 8 still needs that answer written down
            available = {entity_key(a, aliases or {}): none_found() for t in trials
                         for a in t.get("arms", []) if (a["strain_codes"] or a["brand"])  # a nameless arm is the checker's job
                         and any(r["result"] != "not_counted" for r in a["results"])}
        self.write("available.json", {"available": available})
        if search is None:  # by default every trial was found by the felt-stress search
            search = {"felt-stress": [t["pmid"] for t in trials]}
        for cid, pmids in search.items():
            self.write(f"search/{cid}.json", {"condition": cid, "query": "q", "pmids": pmids})
        for t in trials:
            self.write(f"trials/{t['pmid']}.json", t)

    def write(self, rel, data):
        with open(os.path.join(self.path, rel), "w") as f:
            json.dump(data, f, indent=2)

    def cleanup(self):
        self._tmp.cleanup()
