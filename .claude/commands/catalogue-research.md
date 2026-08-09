---
description: Run one research pass for a catalogue entity and write its shard
argument-hint: <strain_id> [shard] | next
---

Run one research pass for the probiotic evidence catalogue and write its shard.

The unit of work is **one pass**, not one entity. A `standard` or `light` entity is a
single pass writing `all.json`; a `deep` entity is one pass per body system, each
writing its own file. A pass never reads or depends on a sibling shard — that
independence is what lets a deep entity's passes run in any order, or at once — with
one exception: **the safety pass is the entity's closing pass.** It runs after every
sibling shard is written and reads them for harm signals, because harms surface inside
efficacy trials and a safety shard blind to its siblings would be a worse safety shard.
Take it last.

## 1. Get the pass plan

If `$1` is empty or `next`, run `python3 tools/plan.py` and take the `next research`
entity. Then:

```
python3 tools/plan.py <strain_id>
```

This prints identity and aliases, any same-species entities (a study of theirs is never
credited here), the triage verdict, which passes the entity owes, which are already
written, and — for each unwritten pass — **the exact set of `impact_id`s that pass may
use**. Take the first unwritten or unfinished pass, or the one named in `$2`. An
unfinished pass is marked `[~]`: written, but still owing targeted searches, with
exactly the owed ids listed — re-opening it means running those searches and recording
each as a claim or a `searched_empty` entry, not redoing the pass.

If the entity has no triage entry, stop and run `/catalogue-triage` first. The pass
plan comes from the depth budget; inventing one commissions research against a budget
nobody set.

## 2. Read the rules

Read `SCHEMA.md`, specifically: **Row grain**, **Fields** (the claim, evidence
strength, practical, provenance), **Evidence tiers** including all six tier rules,
**Source policy**, and **Controlled vocabulary**. Then read `templates/shard.json`,
which has a worked example for each branch of the schema.

These are the spec. This file is only the order of operations.

## 3. Search

Use every name from the plan output: current genus, legacy genus, commercial names.
Under-searching by name is the single most common way a pass misses half a strain's
literature.

Search **within this pass's body systems only**. If the GI pass stumbles on a
gut-barrier mouse study, it records nothing — the mechanistic pass is looking for
exactly that paper and will find it. Nothing is lost, and no pass writes outside its
own file.

Evidence in an **excluded** body system (Skin, Oral, Respiratory, Urogenital) is
recorded nowhere and is *not* raised in `proposed_impacts`. Note that respiratory-tract
*infection* outcomes are `Immune` and remain in scope; only asthma and wheeze left.

## 4. Grade

Grading is done from abstracts, systematic reviews, and meta-analyses. A study is never
excluded for lacking an accessible full text, and a value is never inferred from a
study's design. If a claim's direction cannot be determined from what is accessible,
the claim does not go in the catalogue.

Capture `dose`, `duration`, and `delivery_format` in the same read that yields the
direction and effect size — going back for them after validation costs a second search.
If the abstract omits them and a full text is accessible, take the look; if they are
genuinely unreported, say so in the field per Source policy rather than leaving it
empty.

Four traps, in the order they bite:

**Strain identity is confirmed per study, never assumed from a species name.** Before
grading any study, confirm its exact strain designation in the record itself — the most
cited paper under a species name is routinely a different strain. The same-species
entities and the `triage_notes` trap list the plan prints are a starting point, not an
inventory. A study whose strain cannot be confirmed from what is accessible is excluded
and noted in `gaps`: the catalogue errs toward missing evidence rather than
misattributing it.

**Tier rule 6 is the routine case, not an edge case.** Most systematic reviews in this
field pool at genus or species level. "*Lactobacillus* for AAD, RR 0.60" across twelve
trials of eight strains is not this strain's finding, however convenient the citation.
Check the review's three cases in SCHEMA.md before taking any pooled number. Expect
tier `A` to be rare; that is an honest picture of the literature, not a failure of the
pass.

**A sub-population split is resolved inside the row, never by silence.** Tier rule 5
gives two ways to do it and both require naming which population went which way in
`tier_rationale`.

**Nulls and harms belong here as much as benefits.** A well-run trial showing no effect
for a widely marketed claim is among the most decision-relevant rows the table can
carry. Record everything found and let `evidence_tier` do the filtering.

## 5. Write the shard

Write `strains/<strain_id>/<basename>.json`, copying the shape from
`templates/shard.json`. Copy the shape only: every claim in the template is a worked
example, not a finding, and each one must be deleted, not edited into place — an
example row left behind validates cleanly and publishes an invented finding.

- `impact_id` comes from the plan output's allowed list. Never invent one. If a genuine
  finding has no matching id, put it in `proposed_impacts` with a rationale — check
  `excluded_outcomes` first, since an outcome listed there is out of scope by decision.
- Store **no** identity fields (genus, species, designation, aliases, components) and
  **no** outcome fields (`health_impact`, `body_system`). Both are joined at build time
  from their single source. A shard that stores them creates a second copy that drifts.
- One row per `(impact_id, population)`. Human and preclinical evidence are separate
  ladders, so the same impact may carry both a `humans` and an `animals` row.
- `n_participants: null`, not `0`, when there is no denominator. `0` reads as a
  measured zero.
- A `sources` identifier is written only after resolving it: fetch the PubMed record
  or DOI page and confirm the title matches the study graded. Never transcribe a PMID
  or DOI from a search-result summary, a reference list, or memory — a plausible
  identifier that resolves to the wrong paper, or to nothing, passes validation and
  publishes a citation to a study nobody read.
- `searched_empty` lists every allowed `impact_id` this pass individually searched and
  could not write a row for; the why goes in `gaps`. For a deep pass the remainder —
  allowed minus claimed minus `searched_empty` — is derived debt that re-opens the
  pass, so an empty targeted search that goes unrecorded is a search someone repeats.
- `pass_summary` describes *this pass only* and may not depend on a sibling shard —
  except in the safety pass, which closes the entity and reads its siblings.

**Always write the shard, even when the pass found nothing** — `claims: []` with a
summary saying what was searched and came back empty. A missing shard means the pass
has not run, and that distinction is what `build/coverage.md` reports.

## 6. Verify

```
python3 tools/validate.py <strain_id>
```

Fix anything it reports and re-run until clean. Errors are the 16 documented invariants
plus the parse/shape structure checks, and are defects, not judgment calls. Warnings are not rule violations, but read them:
a missing `population_detail` or `tier_rationale` means the row is unfalsifiable or the
tier is unauditable, and both are cheaper to fix now than to reconstruct later.

## 7. Report

Say what the pass found: the best-supported findings, where the evidence is thin, any
safety signal, and anything that surprised you. If a pooled review forced a row down to
`B` under tier rule 6, or an outcome turned out to have no strain-attributable evidence
at all, that is worth saying out loud rather than leaving in a `tier_rationale`.
