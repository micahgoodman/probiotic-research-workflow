#!/usr/bin/env python3
"""Resolves every cited PMID and DOI and prints the title next to its claim.

    python3 tools/check_citations.py [strain_id ...] [--root]

A plausible identifier is not a citation: a fabricated PMID is perfectly
well-formed, resolves to the wrong paper or to nothing, and passes every offline
check. validate.py stays offline and deterministic on purpose, so this is the
network half of the bargain — an opt-in check, run before a build when the network
allows, never a seventeenth validation rule.

The tool issues exactly two verdicts per identifier: resolved (title printed next
to the claim, so a wrong-paper mismatch is visible to the person reading) and
UNRESOLVED (which fails the check). It never guesses at semantic match.

Exit codes: 0 every identifier resolved; 1 at least one did not — stop and fix the
data; 2 the check itself could not run (network, parse failure) — run it again
later, which is a different instruction from "fix the data".

PMIDs resolve through NCBI esummary in batches; DOIs one at a time through
doi.org content negotiation. Requests are sequential with a courtesy delay, under
NCBI's unauthenticated rate limit. Run it from one place at a time — it belongs to
the session that owns the build, not to research passes.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

from catalogue import Catalogue, Shard, plural

BATCH_SIZE = 200  # NCBI esummary is comfortable with 200 ids per GET
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
TIMEOUT = 30
DELAY = 0.35  # seconds between requests: under 3/s, NCBI's unauthenticated limit


class TransportError(Exception):
    """The check could not run - network down, malformed response. Exit 2."""


class NotFound(TransportError):
    """The endpoint answered: no such document. An UNRESOLVED verdict, not exit 2."""


def default_fetch(url: str, headers: dict) -> str:
    time.sleep(DELAY)
    request = urllib.request.Request(url, headers={"User-Agent": "probiotic-catalogue-check-citations", **headers})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if 400 <= exc.code < 500:
            raise NotFound(f"HTTP {exc.code} for {url}") from exc
        raise TransportError(f"HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise TransportError(f"{exc} for {url}") from exc


# --- collection --------------------------------------------------------------------


def sites(shard: Shard) -> list[tuple[str, str]]:
    """(where, identifier) for every source the shard cites, in file order.

    proposed_impacts count: a proposal's evidence lead seeds a future vocabulary
    row and the research pass that re-opens for it, and a fabricated lead poisons
    both.
    """
    found = []
    for claim in shard.claims:
        where = f"{claim.get('impact_id')}/{claim.get('population')}"
        for source in claim.get("sources") or []:
            if isinstance(source, str):
                found.append((where, source))
    for index, proposed in enumerate(shard.proposed_impacts):
        for source in proposed.get("sources") or []:
            if isinstance(source, str):
                found.append((f"proposed[{index}]", source))
    return found


def parse_identifier(identifier: str) -> tuple[str | None, str]:
    """("pmid"|"doi"|None, value). None means this tool cannot check it, and
    "could not check" must never pass as "checked"."""
    if identifier.startswith("PMID:"):
        value = identifier[len("PMID:"):].strip()
        return ("pmid", value) if value.isdigit() else (None, identifier)
    if identifier.startswith("DOI:"):
        value = identifier[len("DOI:"):].strip()
        return ("doi", value) if value.startswith("10.") else (None, identifier)
    return (None, identifier)


# --- resolution --------------------------------------------------------------------


def resolve_pmids(pmids: list[str], fetch) -> dict[str, str | None]:
    """pmid -> title, or None for a pmid PubMed does not know."""
    titles: dict[str, str | None] = {}
    for start in range(0, len(pmids), BATCH_SIZE):
        batch = pmids[start : start + BATCH_SIZE]
        url = f"{ESUMMARY}?db=pubmed&retmode=json&tool=probiotic-catalogue&id={','.join(batch)}"
        try:
            body = json.loads(fetch(url, {}))
        except NotFound:
            # A 4xx on a batch says nothing per-id; treat every member as unknown.
            body = {}
        except json.JSONDecodeError as exc:
            raise TransportError(f"esummary returned non-JSON: {exc}") from exc
        result = body.get("result") or {}
        for pmid in batch:
            entry = result.get(pmid)
            title = entry.get("title") if isinstance(entry, dict) else None
            titles[pmid] = title if title and not entry.get("error") else None
    return titles


def resolve_dois(dois: list[str], fetch) -> dict[str, str | None]:
    """doi -> title via doi.org content negotiation, or None for no such DOI."""
    titles: dict[str, str | None] = {}
    for doi in dois:
        try:
            body = json.loads(fetch(f"https://doi.org/{doi}", {"Accept": "application/vnd.citationstyles.csl+json"}))
        except NotFound:
            titles[doi] = None
            continue
        except json.JSONDecodeError:
            titles[doi] = None
            continue
        title = body.get("title")
        titles[doi] = title if isinstance(title, str) and title else None
    return titles


# --- the check ---------------------------------------------------------------------


def run(cat: Catalogue, only: list[str] | None, fetch=default_fetch) -> int:
    shards = [s for s in cat.shards if not only or s.dir_name in only]
    per_shard = [(shard, sites(shard)) for shard in shards]

    pmids: list[str] = []
    dois: list[str] = []
    for _, found in per_shard:
        for _, identifier in found:
            kind, value = parse_identifier(identifier)
            if kind == "pmid" and value not in pmids:
                pmids.append(value)
            elif kind == "doi" and value not in dois:
                dois.append(value)

    try:
        pmid_titles = resolve_pmids(pmids, fetch)
        doi_titles = resolve_dois(dois, fetch)
    except TransportError as exc:
        print(f"check could not run: {exc}")
        return 2

    n_sites = 0
    unresolved = 0
    for shard, found in per_shard:
        if not found:
            continue
        print(f"\n{shard.rel}")
        for where, identifier in found:
            n_sites += 1
            kind, value = parse_identifier(identifier)
            if kind == "pmid":
                title = pmid_titles.get(value)
            elif kind == "doi":
                title = doi_titles.get(value)
            else:
                title = None
            if title is None:
                unresolved += 1
                reason = "no such record" if kind else "not a PMID: or DOI: identifier"
                verdict = f"UNRESOLVED ({reason})"
            else:
                verdict = title if len(title) <= 120 else title[:119] + "…"
            print(f"  {where:<40} {identifier:<24} {verdict}")

    n_unique = len(pmids) + len(dois)
    print(
        f"\n{plural(n_sites, 'identifier')} ({n_unique} unique), "
        f"{unresolved} unresolved"
    )
    return 1 if unresolved else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("strain_id", nargs="*", help="limit the check to these entities")
    parser.add_argument("--root", help="catalogue root (default: $CATALOGUE_ROOT or repo)")
    args = parser.parse_args(argv)

    cat = Catalogue.load(args.root)
    if cat.parse_errors:
        # Unreadable data cannot be checked, only reported - same reasoning as
        # validate.py, but with the "run again later" exit code because the fix
        # is elsewhere.
        for rel, message in cat.parse_errors:
            print(f"cannot read {rel}: {message}")
        return 2
    return run(cat, args.strain_id or None)


if __name__ == "__main__":
    sys.exit(main())
