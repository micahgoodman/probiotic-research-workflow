---
description: Validate the catalogue and regenerate build/ (CSV, readable view, coverage)
---

Compile the probiotic evidence catalogue.

When the network allows, check citations first:

```
python3 tools/check_citations.py [strain_id ...]
```

Opt-in and network-bound, which is why it is not a seventeenth validation rule: a
fabricated PMID is perfectly well-formed and passes every offline check. The tool
resolves every cited PMID and DOI and prints the resolved title next to its claim —
read the titles, because resolves-to-the-wrong-paper looks exactly like success until a
person does. Exit 1 means an identifier did not resolve: stop and fix the data before
building. Exit 2 means the check itself could not run (network, parse failure): run it
again later, and build anyway if the build cannot wait — the data has not been shown
wrong. It runs serially from this session, never from research passes: concurrent runs
queue against NCBI's unauthenticated rate limit.

Then build:

```
python3 tools/build.py
```

This runs the 16 validation rules, then writes `build/catalogue.csv`,
`build/catalogue.md` and `build/coverage.md`. It refuses to write anything if a rule
fails: the compiled views are the surface people read, so they are never generated from
data already known to be wrong.

If it refuses, fix the data — never the output. Files in `build/` are regenerated and
a hand-edit there is lost on the next run.

Then report:

- what changed in scope: how many claims, across how many entities
- where the catalogue stands, from `build/coverage.md`: what is untriaged, what is
  half-researched, and which passes ran and found nothing
- any **proposed impacts awaiting reconciliation**. These are outcomes a research pass
  found with no matching `impact_id`. Adding one to `vocabulary/outcomes.json` is a
  deliberate step and is never done by the pass that proposed it — bring them to the
  user rather than resolving them silently. When one is accepted, the reconciler does
  exactly three things: adds the id to the vocabulary, clears the proposal, and leaves
  its source leads in the shard's `gaps`. Nothing more — the new id enlarges the
  allowed set of the deep passes it lands in, so the derived-debt arithmetic re-opens
  exactly the passes that now owe it a targeted search, with no follow-up bookkeeping.
- any **validation warnings**. They do not block a build, but they are the fields the
  tier rules lean on. A cluster of them in one area usually means a research pass was
  rushed rather than that the schema is wrong.

`python3 tools/plan.py` gives the same status without rebuilding, if that is all you
need.
