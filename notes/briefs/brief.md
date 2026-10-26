# Research brief — probiotic catalogue, version 2

Working directory: the catalogue root, the folder that holds `RULES.md`.

## What you are doing

You read the papers on your list and write one small JSON file for each one. You do not
judge how good a paper is. You do not weigh evidence. The program does all of that from
the files you write. Your only job is to record what the paper says, using the fixed words
in the rules.

**Read `RULES.md` in the working directory first, all of it. It is short.** This brief only
adds the mechanics. Where this brief and `RULES.md` disagree, `RULES.md` wins.

`conditions.json` holds the six conditions and, for each one, the list of scores that count.
Read it before you start. Only a score on that list can carry a result.

## The files you write

One file per paper: `<your output folder>/<pmid>.json`. Your task message names your output
folder and your papers. **Write nothing anywhere else.** Do not touch `RULES.md`,
`conditions.json`, `aliases.json`, `search/`, `tools/` or any paper not on your list.

A paper that fails an eligibility test in Rule 3:

```json
{"pmid": "12345678", "status": "excluded", "excluded_reason": "not_human"}
```

A paper that passes every test:

```json
{"pmid": "12345678",
 "status": "eligible",
 "design": "randomized_placebo",
 "registration": "NCT01234567",
 "n_randomized": 100,
 "population": "healthy university students",
 "arms": [
   {"entity_as_stated": "Lactobacillus plantarum PS128, 3x10^10 CFU capsule",
    "strain_codes": ["PS128"],
    "brand": null,
    "other_actives": [],
    "preparation": "live",
    "dose_as_stated": "3x10^10 CFU per day",
    "weeks": 8,
    "results": [
      {"condition": "felt-stress", "result": "benefit", "instrument": "pss",
       "comparison": "between_groups", "main_endpoint": "yes"},
      {"condition": "anxiety", "result": "not_counted", "reason": "not_measured"}
    ]}
 ]}
```

Rules about the shape, all of which the checker enforces:

- Every field above must be present. No extra fields. `registration` is `null` when the
  paper names no trial registration number. `n_randomized` is `null` when you cannot find
  the number; never `0`.
- **One arm object per treatment arm.** The placebo arm is not an arm here — it is the
  comparison. A three-arm trial of two different products gives two arm objects.
- **Every condition whose search list holds your paper needs a result.** Your task message
  tells you which lists each paper is on. `{"result": "not_counted", "reason": "not_measured"}`
  is a complete and correct answer, and it is the most common one.
- You may also record a condition the paper measured that is not on its search lists. That
  is welcome but not owed.

## The five decisions, and nothing else

For each arm and each condition, you decide five things and you never argue in prose:

1. **Is the paper eligible?** Rule 3. If not, one reason code and you are done with it.
2. **What is the design?** One of `randomized_placebo`, `randomized_other_control`,
   `not_randomized`, `single_group`. A weak design is never a reason to exclude a paper.
3. **Which score did they use?** It must be on that condition's list in `conditions.json`.
   If they used something else, `{"result": "not_counted", "reason": "instrument_not_listed",
   "instrument_as_stated": "<the name the paper uses>"}`. Write the paper's own words there.
4. **What did that score show?** `benefit`, `no_difference` or `harm`. For cortisol, a lower
   level is `benefit`. Follow the Results section and the tables, not the abstract's summary
   sentence, when you have the full text.
5. **What was it compared against?** `between_groups` (against the control group),
   `within_group` (against the same people before the trial), or `not_stated`. **If the paper
   does not say, `not_stated` is the answer. Never assume "versus placebo".** This is the
   single most common real error found in the old version of this catalogue. When a paper
   gives both comparisons for the same score, `between_groups` wins.

Also `main_endpoint`: `yes`, `no` or `not_stated` — was this the trial's stated main measure?

## The eight things the pilot of 20 September 2026 showed were easy to get wrong

Two researchers recorded the same 30 papers. They agreed on all 30 eligibility decisions.
These eight points are every place they disagreed, and each is now a fixed rule.

1. **A fibre, a food or a medicine with no bacteria in it is `not_a_probiotic`**, not
   `not_an_intervention_study`. The searches return prebiotic-only trials in bulk because of
   the words "synbiotic" and "postbiotic".
2. **The Rule 3 tests run in table order and the first failure wins.** Two true reason codes
   for one paper is a defect.
3. **When the abstract names no strain and no brand, and the full text is closed, the reason
   is `not_accessible`, not `entity_not_named`.** Never say a paper named no strain when
   nobody could look in the Methods.
4. **`n_randomized` is the number put into groups before dropout.** If the paper gives only
   the number who finished or were analysed, use that. Never `0`.
5. **`main_endpoint` is `yes` or `no` only when the paper says "primary endpoint", "primary
   outcome" or the same idea in plain words.** A stated aim is not a primary endpoint;
   that is `not_stated`. **A score the paper calls a "secondary endpoint" or "secondary
   outcome" is `no`** (user decision, 21 September 2026): "secondary" is the plain-words
   opposite of primary, so the paper has said it. The flag is recorded for the reader and
   for future rule changes; it never decides which score speaks for a trial.
6. **When a paper reports two or more listed scores for one condition, record EVERY one of
   them as its own result entry, each with its own `result`, `comparison` and
   `main_endpoint`.** You never pick. The program picks the one nearest the top of the list
   (user decision, 21 September 2026; this replaces the old "record only the winner" rule).
   The same score may not appear twice for one entity. **The list wins even against the
   trial's own primary endpoint** (user decision, 21 September 2026), so never move a score
   up because the paper calls it primary — just record them all.
   **A listed score with no total score, such as the OSA-MA, is still a listed score**
   (user decision, 21 September 2026). Where a label in `conditions.json` says "total score"
   or "global score", a total is required; where the label names the instrument alone, a
   whole-instrument verdict counts. Its individual factors are still `subscale_only`.
7. **A score measured in a parent, carer or partner is `not_measured`.** The catalogue is
   about the people who took the probiotic.
8. **`between_groups` needs a reported test between the groups.** A sentence saying the
   groups were "comparable", with no test anywhere in the paper, is not one. Record the
   within-group result the paper does give, as `within_group`.

Wave 1 added five more, all now in RULES.md:

12. **A control that is the same thing without the bacteria is a placebo**, whatever the
    paper calls it. "Control milk" against the same milk fermented with the strain is
    `randomized_placebo`. Use `randomized_other_control` only when the other group took
    something genuinely different: nothing, another medicine, or a diet.
13. **"Measured one of the six conditions" means measured at all**, not measured with a
    listed score. A trial that measured sleep on its own diary stays eligible and gets
    `instrument_not_listed`. `no_listed_condition` is only for a paper that measured none
    of the six.
14. **"The first report of this trial" means the first report of its results.** A protocol
    is not a report, so the results paper is still the first report.
15. **A retracted paper is `excluded` / `retracted`.** The program clears most of these
    before you see them, but if you meet one, that is the code.
16. **A network trap that cost one researcher eleven wrong full texts:** when PubMed has no
    free copy of a paper, `elink` returns a `pubmed_pmc_refs` list, which is papers that
    *cite* yours. Taking the first link gives you an unrelated article. Always check that
    `linkname == "pubmed_pmc"`, and check the title you get back matches.

Three more rules were settled by the user on the same day:

9. **A validated short form counts as the score it shortens.** Its name is in that score's
   `aliases` in `conditions.json`. A short form is not a subscale; a subscale is still
   `subscale_only`.
10. **Child scores are on the lists now** — SDSC for sleep, Bayley-III and WPPSI for
    cognition. A child trial counts like any other.
11. **Cognition still takes whole-test overall scores only.** A trial that reports only
    single tasks, with no overall score, is `instrument_not_listed`. This is deliberate: a
    trial reporting eight tasks will nearly always have one that looks good by chance.

## Things that are easy to get wrong

- **`entity_as_stated` is a short name, not a sentence.** It is what appears in the
  "Probiotic" column of the finished page, so keep it to the product or strain name and its
  codes: "Lactiplantibacillus plantarum HEAL9", "Vivomixx (eight strains)", "Lacticaseibacillus
  rhamnosus HN001". **The dose goes in `dose_as_stated` and nowhere else.** A dose written
  into the name makes the page unreadable and stops two trials of the same product joining
  into one row.
- **The entity is the difference between the groups** (Rule 4). If both groups got vitamin D
  and only one got the strain, `other_actives` is empty, because vitamin D is not the
  difference. If only the treatment group got it, it goes in `other_actives`.
- **A blend is not its parts.** A four-strain product gives one arm with four `strain_codes`.
  It never counts as evidence for any one of those strains.
- **`strain_codes` are codes**, as the paper prints them: `["PS128"]`, `["CECT 7765"]`,
  `["NCIMB 30242"]`. Not the species name. If the paper names only a brand and no code, leave
  `strain_codes` empty and fill `brand`. If it names neither, the paper is
  `excluded` / `entity_not_named`. A blend is named only when every strain in it has a
  code or the product has a brand: "GG plus an unnamed B. longum" is `entity_not_named`,
  never a record under GG alone (ruled 18 October 2026).
- **One dose only.** If a trial tested two doses of the same thing, record the highest dose.
- **`other_actives` holds only what the trial added on top of the product** (user decision,
  21 September 2026). If the product is sold with a prebiotic or a vitamin already in it,
  do not list it. The brand name already means the whole product, and listing its own
  ingredients again splits one product into several entities.
- **The coating and the vehicle never change the entity** (user decision, 21 September 2026).
  A coated and an uncoated capsule of one product are one entity, as are a yoghurt and a
  capsule of one strain.
- **Heat-killed, tyndallized or "non-viable" is `preparation: "heat_killed"`.** Everything
  else is `"live"`.
- A subscale of a listed questionnaire is not the listed score: `reason: "subscale_only"`.
  A result given only for a subgroup is `reason: "subgroup_only"`.

## Honesty rules — these matter more than coverage

- **Never bypass or solve a CAPTCHA or any other bot-detection, and never try to get around a
  paywall.** If you cannot read the paper, write
  `{"pmid": "...", "status": "excluded", "excluded_reason": "not_accessible"}` and move on.
  If you can read the abstract but not the number you need for one condition, that condition
  gets `{"result": "not_counted", "reason": "result_not_accessible"}`.
- **Never invent a figure or a strain code.** A recorded gap is worth more than a guess.
- If the abstract and the Results disagree, follow the Results and say so in your report.

## Network

Sleep 1 to 2 seconds between NCBI calls.

```
CA=<path to a CA bundle, if your network needs one>
curl -s --cacert $CA "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<pmid>&retmode=xml"
curl -s --cacert $CA "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:<pmid>&resultType=core&format=json"
curl -s --cacert $CA "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<numeric>&retmode=xml"
```

## Do not run these

**Do not run the test suite, `tools/build.py`, or any dev server or build.** The main session
runs those once, alone, and owns the result. You may run
`python3 tools/validate.py <your pmids>` to check your own files only if your output folder is
`trials/`; if your folder is somewhere else, do not run it at all — just follow the shape above.

## Report back

A table: pmid, `excluded` with its reason, or `eligible` with the entity and one line per
condition saying what you recorded. Then, separately:

1. **Anything you decided rather than knew.** List every judgement call in full, with the
   paper, so it can be overruled. This is the most valuable part of your report.
2. Any paper where two of the five decisions above could each be defended. Say which two.
3. Any score you met that is not on the list in `conditions.json` and that you think should be.
4. Anything blocked, and what blocked it.

## Wave 2 added four rulings (21 September 2026)

17. **A secondary report points at the trial's own record, never at another follow-up
    paper.** If the paper you would point at is itself a `secondary_report`, point at
    what it points at. The checker now refuses a chain, so you will see an error.

18. **A shared registration number is not an error and not a reason to exclude.** Mark a
    paper `secondary_report` only when the paper itself reports a trial already reported.
    Write the registration exactly as the paper prints it; never edit a number to dodge a
    collision. The screening report lists shared numbers for a reader (18 October 2026).

19. **`result_not_accessible` covers two cases**, and this is settled: the paper does not
    say whether the change was significant, OR the paper says a score moved but never
    names which score. Do not raise this again; one code is the user's choice.

20. **New scores are on the lists.** depression gained `cdi` (Children's Depression
    Inventory), `zung-sds`, `poms-total` (POMS total mood disturbance) and
    `panas-negative` (the PANAS NEGATIVE affect scale only — PANAS has no total, and on
    its positive affect scale a good result is a higher score, which depression would
    read as harm. A paper reporting only positive affect is instrument_not_listed).
    anxiety gained `scared`, `scas` and `zung-sas`. Check conditions.json, not memory.

21. **A faecal transplant taken by mouth is `entity_not_named`.** Donor stool is live
    bacteria, so it passes the probiotic test, then fails the naming test, because donor
    microbiota has no strain code or brand by its nature. Access to the full text makes
    no difference. By colonoscopy or enema it is `not_oral` instead.

22. **"Everyone who joined" means intention to treat.** When a paper reports both the
    full-set analysis and a smaller one (completers, per protocol, modified ITT), record
    the full-set result. When it reports only a smaller set, record that. When it ran the
    full-set analysis but prints only the smaller set's figure for a score, that score is
    `result_not_accessible` (ruled 18 October 2026).

23. **Record every condition the paper measured, not only the one your search asked
    about.** A result for a condition the paper was on no list for counts the same
    (ruled 18 October 2026). The checker allows extra conditions.

24. **Fifteen scores joined the lists on 18 October 2026** (PAS, PRAS-ASD, ASC-ASD, the
    Goldberg scale's two scores, CBCL anxiety problems, GDS, PROMIS depression, the
    Levenstein PSQ, ESS, PDSS, PHES, Mullen composite, and the two child sleep
    questionnaires CSHQ and Sleep Self-Report). Check conditions.json, not memory.
    A score joins a list only by the four tests in RULES.md rule 5; if your
    `instrument_as_stated` names a score that is on that condition's list, the screening
    report will mark the record for re-reading.

25. **The result is the one at the trial's own stated endpoint.** A between-group win at an
    earlier time point, with no readable figure at the endpoint, is `result_not_accessible`
    (PMIDs 41679635, 26419583, 28101105). Do not take the one time point that worked.

26. **A cortisol level beats a cortisol response to a laboratory stress test.** When a paper
    reports both, record the level (resting or awakening sample at the endpoint); the
    change during a Trier or Maastricht test is a different quantity (PMID 37513541).

27. **A look back at people treated outside the study is `not_an_intervention_study`**,
    like a cohort or a registry (PMID 38240683, a retrospective Colicron series).
