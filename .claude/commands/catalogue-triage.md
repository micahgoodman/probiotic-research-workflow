---
description: Triage one roster entity - estimate its literature and assign a depth budget
argument-hint: <strain_id> | next
---

Run the triage stage for one entity of the probiotic evidence catalogue.

Triage is a cheap pass that answers two questions: **how much literature is there**
(so the research stage can size its effort) and **does this entity actually belong on
the roster** (criteria 2 and 3, which assembly could only guess at). It produces no
claim data. Its counts are budget estimates and are never a source for a claim's
`n_studies` or `n_participants`.

## 1. Pick the entity

If `$1` is empty or `next`, run `python3 tools/plan.py` and take the `next triage`
entity. Otherwise use `$1`.

Then read its identity and provenance:

```
python3 tools/plan.py <strain_id>
```

## 2. Read the rules

Read `SCHEMA.md` sections **Triage**, **Scope**, and **Roster assembly** (the four
inclusion criteria). Do not work from memory of them; they are the spec and this file
is only the procedure.

## 3. Search

Search PubMed and the wider literature for the strain. Use **every name** from the
plan output — current genus, legacy genus, and commercial names. The 2020 split of
*Lactobacillus* into 25 genera means a search under one name alone misses much of the
corpus, and a Japanese or European product often has more trials under its brand name
than its designation.

Establish, approximately:

- how many systematic reviews or meta-analyses cover it
- how many human RCTs exist
- which **in-scope** body systems have human evidence
- whether notable claims rest on animal work alone

Count studies, not search hits: a PubMed result count includes comments, errata, and
reviews of reviews. Approximate is fine and expected — this is a budget, not a finding.

## 4. Confirm the entity belongs

This is the part assembly could not do, so do it explicitly and record the answer
either way.

**Criterion 3 (evidenced)** is the one that keeps the roster honest. A `drop` is
confirmed, never inferred from `known_for` — that field is a search starting point and
strains routinely have trial evidence it omits. This matters most for entities whose
place was earned in a body system now out of scope: GR-1, RC-14, CTV-05 and
*S. salivarius* M18 read as entirely out of scope, while K12 and CECT 5716 keep in-scope
evidence (otitis media and URTI; infant infections) behind an out-of-scope headline.
Look for in-scope evidence in each and record what you found, including "none".

**Criterion 2 (consumer-available)** matters most for the nine entities whose
`roster_source` is `recall (pre-sweep)` — neither sweep surfaced them, which is a
signal rather than a verdict. Several are simply outside the US/UK/Canada markets the
guides cover.

**Preparation.** Check which preparation the trials actually used. `preparation` is
part of identity, not an annotation: the same strain live and heat-inactivated are two
entities with two evidence bases. One roster entry was already wrong this way
(CP2305, marketed heat-inactivated). If the trials split across preparations, say so
in `triage_notes` — the research stage has to know which trial belongs to which entity.

## 5. Assign a depth

Per SCHEMA.md's depth budgets: `deep`, `standard`, `light`, or `drop`. Record only
in-scope body systems in `outcome_areas`; if an excluded system bears on the depth
call, note it in `triage_notes` instead.

`outcome_areas` is what commissions research passes, so it decides how much work
happens. A `deep` entity gets one pass per area listed plus a mechanistic and a safety
pass always.

## 6. Record it

```
python3 tools/triage.py record --json '{
  "strain_id": "...",
  "n_systematic_reviews": 0,
  "n_human_trials": 0,
  "has_preclinical_only_areas": false,
  "outcome_areas": ["GI"],
  "depth": "standard",
  "triage_notes": "What was searched, what was found, and how criteria 2 and 3 were confirmed."
}'
```

The tool refuses anything it would otherwise have to warn about later — an unknown
`strain_id`, an out-of-scope `outcome_area`, empty `triage_notes`. Fix and re-run; do
not edit `triage.json` by hand, because every triage pass appends to that one file and
a hand-edit can silently discard another pass's entries.

`triage_notes` is not optional padding. It is the only record of why this depth was
chosen, and the person revisiting it will not be the person who chose it.

## 7. If the verdict is `drop`

Record the verdict first (step 6, with `"depth": "drop"`), then move the entity:

```
python3 tools/triage.py drop <strain_id> "Criterion N fails: ..."
```

This keeps the `strain_id` in `excluded_entities` so the next sweep can recognise that
it re-proposed something already settled. The triage entry stays behind on purpose —
it is the evidence the drop was confirmed rather than inferred.

## 8. Verify

```
python3 tools/validate.py <strain_id>
```

Report what you found: the depth, the counts, which criteria you confirmed and how,
and anything the research stage will need to know. If the entity surprised you —
evidence in a system nobody expected, a preparation mismatch, a designation that turns
out to be shared — say so rather than only recording it.
