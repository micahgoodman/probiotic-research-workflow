"""Run the fixed PubMed search for each condition and save the list of papers (RULES.md rule 2).

A saved list only grows. PubMed re-indexes papers, and a paper that has a record must never
fall off its list. Needs the network; set SSL_CERT_FILE if your network needs a CA bundle.
"""
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import catalogue as C

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=9999&term="


def build_query(search, condition):
    return (f"{search['probiotic_terms']} AND {condition['pubmed_terms']} AND {search['study_terms']} "
            f"{search['human_terms']}")


def merge(old, new):
    return sorted(set(old) | set(new), key=int)


def fetch_pmids(query):
    with urllib.request.urlopen(ESEARCH + urllib.parse.quote(query), timeout=60) as resp:
        found = json.load(resp)["esearchresult"]
    if int(found["count"]) != len(found["idlist"]):
        raise SystemExit(f"PubMed has {found['count']} papers but returned {len(found['idlist'])}; raise retmax")
    return found["idlist"]


def main():
    root = C.root_dir()
    config = C.read_json(os.path.join(root, "conditions.json"))
    os.makedirs(os.path.join(root, "search"), exist_ok=True)
    for condition in config["conditions"]:
        path = os.path.join(root, "search", condition["id"] + ".json")
        old = C.read_json(path)["pmids"] if os.path.exists(path) else []
        query = build_query(config["search"], condition)
        pmids = merge(old, fetch_pmids(query))
        with open(path, "w") as f:
            json.dump({"condition": condition["id"], "query": query,
                       "last_run": datetime.date.today().isoformat(), "pmids": pmids}, f, indent=2)
            f.write("\n")
        print(f"{condition['id']}: {len(pmids)} papers ({len(pmids) - len(old)} new)")
        time.sleep(1.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
