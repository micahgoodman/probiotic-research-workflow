# Probiotic Evidence Catalogue

A strain-level catalogue of what the research actually shows about the health effects of
consumer probiotic preparations. `SCHEMA.md` is the design: row grain, fields, evidence
tiers, scope, source policy, and the 16 validation rules. This file is how to run it.

## The workflow

Research proceeds one entity at a time, in three stages. Each stage has a slash command
holding its procedure, and a tool holding the parts that must be mechanical.

| Stage | Command | Writes |
|---|---|---|
| **Triage** — how much literature is there, and does this entity belong? | `/catalogue-triage <strain_id>` | `triage.json` |
| **Research** — one pass, graded and written | `/catalogue-research <strain_id> [shard]` | `strains/<strain_id>/<shard>.json` |
| **Build** — validate and compile | `/catalogue-build` | `build/` |

Start anywhere with:

```bash
python3 tools/plan.py            # progress, and the next entity for each stage
```

Triage must precede research, because the depth budget decides how many passes an
entity gets. Everything else can be done in any order.

## Current phase

Triage the whole roster before running more research passes. The pilot entity
(`lacticaseibacillus-rhamnosus-gg`) has been researched end-to-end to prove the
workflow; what research runs next should come from comparing depth budgets across the
full roster, not from whichever entity happens to be triaged. Full triage also writes
every entity's `triage_notes` trap list — the confusable-strain warnings research
passes lean on — and surfaces drops before research hours are spent near them.
`python3 tools/plan.py` names the next entity to triage.

## Tools

All stdlib Python 3, no dependencies. Run from anywhere; they locate the catalogue via
`$CATALOGUE_ROOT` or their own checkout.

```bash
python3 tools/plan.py                       # status + what to do next
python3 tools/plan.py <strain_id>           # identity, triage verdict, pass plan,
                                            #   and the impact_ids each pass may use
python3 tools/validate.py [strain_id ...]   # the 16 rules; exit 1 on any violation
python3 tools/triage.py record --json '...' # upsert a triage verdict
python3 tools/triage.py drop <id> "reason"  # move a dropped entity off the roster
python3 tools/build.py                      # validate, then regenerate build/
python3 tools/check_citations.py [id ...]   # network check, opt-in: resolve every
                                            #   cited PMID/DOI and print its title
```

Two of these exist because the operation is unsafe by hand rather than merely tedious:

- **`triage.py record`** — `triage.json` is one file every triage pass appends to.
  Unlike a shard it has no exclusive owner, so two passes that each read-modify-write it
  lose one set of entries with no error. `record` locks, merges by `strain_id`, and
  replaces atomically.
- **`triage.py drop`** — moving an entity to `excluded_entities` has to leave its
  `strain_id` behind, or the next sweep re-proposes it with nothing to match against. It
  also refuses unless triage recorded `depth: "drop"` first, because SCHEMA.md requires
  a drop to be confirmed rather than inferred.

Shards need no tool. One pass owns one file, which is the point of sharding.

## Validation

`tools/validate.py` reports two classes, and the difference is deliberate:

- **Errors** are the 16 rules in SCHEMA.md, plus two structural classes that precede
  them: `parse` (a file unreadable as its documented shape) and `shape` (a field or
  entry without its documented type). They are defects in the data, and `build.py`
  refuses to write anything while one stands.
- **Warnings** are everything else worth saying: prose the rules cannot check, and
  triage or vocabulary values that are readable but unhelpful. They never block a
  build and are collected into `build/coverage.md`. The line between the two classes
  is whether the defect is representable in a finished catalogue — a row whose tier
  nobody justified is thin research, while a row whose `direction` is unreadable is
  broken data.

Where a rule references a value ("tier A requires…", "`study_type` agrees with
`population`"), that value's domain is checked as part of the rule. An unrecognised
`population` would otherwise match none of rule 4's branches and silently switch the
rule off — a validator reporting success on a row it never checked.

## Tests

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'
```

`test_validate.py` breaks one invariant per test and asserts the rule that exists to
catch it fires — a validator nobody has tried to fool is a validator nobody knows works.
`test_build.py` pins the two joins: it renames a label in `vocabulary/outcomes.json` and
asserts the compiled views follow without a shard being touched, because that property
is what the storage design was bought with.

## Layout

```
SCHEMA.md                       design: grain, fields, tiers, scope, the 16 rules
roster.json                     the entities, each with the sweep that found it
                                  — and the only home for entity identity
vocabulary/outcomes.json        controlled outcome vocabulary
                                  — and the only home for labels and body systems
triage.json                     depth budget per entity (generated)
templates/shard.json            annotated skeleton for one research pass
strains/<strain_id>/<shard>.json    source of truth for claims
build/                          compiled, regenerated, never hand-edited
tools/                          plan, validate, triage, build + tests
```

A claim row stores `impact_id` and nothing else about the outcome; a shard stores
`strain_id` and nothing else about the entity. Both are joined at build time. That is
why renaming an outcome is a one-line edit rather than a search across every shard that
used it, and validation rules 2, 3 and 11 exist to keep it that way.

## Note on the slash commands

They live in `.claude/commands/` here, so they are available when Claude Code is started
from this directory. If you work from the parent directory and they do not appear, the
files still hold the full procedure — read the relevant one and follow it.
