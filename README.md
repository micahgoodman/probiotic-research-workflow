# Probiotic Evidence Catalogue

This workflow explores which probiotics have been
tested in people, what the studies found, and how strong the evidence is. The initial outcomes covered by the investigation are stress, cortisol, anxiety, sleep, depression, and cognition.

The result is a table of rows. One row is one probiotic (a strain, a blend, or a named
product) for one condition, with a tier that counts the evidence and a verdict that says what
the studies found. Nobody enters a tier or a verdict – people record facts about each paper,
and a program computes everything else from fixed rules.

## Read the catalogue

- `build/catalogue.md` is the catalogue. It comes in two parts: probiotics a reader can buy
  today, with one product page each, and then everything else.
- `build/catalogue.csv` holds the same rows as a table, one row per probiotic and condition.
- `build/screening.md` lists every paper the searches found and says why each one was kept
  or set aside.

## How to read a row

The tier says how much evidence exists. It does not say how good the result was.

| Tier | Meaning |
|---|---|
| B | two or more randomized trials compared the probiotic with a placebo group |
| C | exactly one such trial |
| D | no such trial, only weaker studies (no placebo group, no random assignment, or a change inside one group) |

The verdict says what the counted studies found, by counting them: "benefit in all 2
trials", "mixed: benefit in 4 of 7 trials", "no difference found in the one trial". Benefit
means the probiotic group's score moved in the right direction compared with the placebo
group at the trial's stated endpoint, on one fixed score per condition. "People" is the total
number of people randomized across the counted trials, and it matters: one trial of 28 people
and one of 500 both read "benefit in the one trial".

## How it was made

1. One fixed PubMed search per condition (`conditions.json`) finds the papers. The saved
   lists are in `search/`.
2. Every paper found gets one record in `trials/<pmid>.json`. A record holds facts: the
   design, how many people were randomized, what each group took, and the result on each
   listed score. When a paper does not fit a rule, the record says why with one fixed code.
3. `tools/build.py` reads the records and writes the catalogue. `RULES.md` is the only
   rulebook. Every rule in it is mechanical, and the program applies it the same way to
   every record.

Studies about the candidate strains were found and reviewed by AI agents as part of an
automated workflow. The records were then checked by class rather than one by one: each rule
was swept across every record by a script, a blind second reading of a sample measured the
disagreement rate, and the maintainer ruled on every open question. The dated decision
sections at the end of `RULES.md` are the audit trail. Mistakes in single records remain
possible. Every record names its PubMed id, so any row can be checked against the paper.

## Known limits

- The searches were last run in September 2026. Papers published since then are missing.
- "Available to buy today" means one consumer product page existed on the date shown. Pages
  change, and nothing more is promised.
- A trial that reports a win at an earlier time point but no figure at its stated endpoint
  counts as "result not accessible", not as a benefit. The same holds for a figure printed
  only inside an image.
- The rest of the known limits, each with the rule it belongs to, are written in `RULES.md`.
  Open items wait in `notes/open-questions.md`.

## Run it

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'   # the tests
python3 tools/validate.py                                    # check every record
python3 tools/build.py                                       # check, then write build/
SSL_CERT_FILE=<ca-bundle> python3 tools/search.py            # refresh the saved paper lists
SSL_CERT_FILE=<ca-bundle> python3 tools/prescreen.py         # clear reviews and the like by PubMed labels
python3 notes/scripts/shape-scan.py                          # look for two shapes of record error
```

Python 3 with no third-party packages.

## Add or fix a paper

Write or edit `trials/<pmid>.json` following `RULES.md`, then run the checker and the build.
The checker refuses a record that breaks a rule, and the build recomputes every row. The brief
given to readers, `notes/briefs/brief.md`, walks through a record field by field.

## Files

| Path | What it is |
|---|---|
| `RULES.md` | the rulebook, with the file layout and every dated decision |
| `conditions.json` | the six conditions, their search words and their ranked scores |
| `aliases.json` | names that mean one strain or product, each with a source in `notes/alias-sources/` |
| `available.json` | one product page per probiotic, or the record that none was found |
| `search/` | the saved list of papers for each condition |
| `trials/` | one record per paper, 1,117 in all |
| `tools/` | the program and its tests |
| `build/` | the catalogue and the screening report, written by the program |
| `notes/` | the decision record: open questions, score admissions, alias sources, status |
