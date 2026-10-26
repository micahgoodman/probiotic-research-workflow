<!-- rewritten 18 October 2026 by class; the September item numbers are kept so older notes still point at them -->
# Open questions, by class

Sixty-seven items came out of the September 2026 waves, one paper at a time. On 18 October
2026 they were sorted into the classes below, and each class was closed by one ruling, one
known limit or one scan, not item by item. The numbers are the September numbers. Status
words: CLOSED (and what closed it), KNOWN LIMIT (where it is written), OPEN (what would
close it), FOR YOUR EYE (rule-correct, worth one look). Every record item names its entity
and says "available" (on the "Available to buy today" page, so first run) or "not available"
(second run). What is still open is collected at the end.

## 1. Shared registration numbers — CLOSED 18 October 2026
Ruling (rule 3): a shared number is never an error; `build/screening.md` lists every number
that sits on more than one eligible record. Across 193 registered records the old guard had
caught no double count and raised two false alarms, one of which kept a 240-person trial out
of the catalogue for 27 days.
- 8 (NCT04452253: 35924970 PS23 and 33842519 PS128): CLOSED, both stand, the number is
  listed. heatkilled+ps23 not available; ps128 available.
- 18 (NCT03259971: 34835954 and 38361371, PS128 in two diseases): CLOSED, listed. ps128
  available.
- 41 (42059569, Lactofem in 240 men, excluded as a duplicate of 38216917): CLOSED, restored
  as its own eligible record; lactofem depression is now "benefit in all 2 weaker studies"
  (352 people). lactofem not available.
- 24 (the guard broke validate.py): CLOSED, the guard and its tests are gone.
- 27 (39417900 prints "NCTO4639141"): CLOSED, the corrected number stays; a registration
  now feeds only the screening list, and nothing computes on it.

## 2. Results for conditions the search did not ask about — CLOSED 18 October 2026
- 50 (36815026, 38068763, 42196985 and the older cases): CLOSED, rule 2 says such a result
  counts, and a test pins it. Dry run before the ruling: 37 of 39 such results were already
  counted, so nothing moved. Known limit, written in rule 2: 154 of 338 eligible records
  answer one condition and 1,352 of 2,028 record-condition pairs are unanswered, so a paper
  read for one condition may hold evidence for another.

## 3. Which analysis set and which time point — CLOSED, with one known limit
- 39 (40583505, MoCA benefit in completers only): CLOSED, `result_not_accessible` under
  rule 6's intention-to-treat sentence (the full-set figure is behind a paywall).
  cuscutaseedextract+heatkilled+mt104, not available, no rows.
- 35654766 (from the wave-2 fix log: benefit only in the modified set): CLOSED, stays
  `no_difference`. Eight-strain DSM key, available.
- 29 and 49 (41679635: cortisol wins at week 5 of 8; PSQI unreadable): CLOSED by the
  endpoint sentence written into rule 6 today; both stay `result_not_accessible`. oll2716,
  not available. The full text sits behind a bot check; a person with access could read the
  week-8 figure.
- 26419583 and 28101105 (same shape): CLOSED, same sentence.
- KNOWN LIMIT (rule 6): the backward sweep for papers that report two analysis sets has
  not been worked; grep cannot find them.

## 4. Naming the product — CLOSED, with three known limits
Rulings (rules 3 and 4): a blend is named only when every strain in it is named; a brand is
the name a product is sold under, so a maker's name is not a brand; a brand or a second
code joins its strain codes by alias when a source publishes the join and the product has
not changed. `notes/scripts/shape-scan.py` finds arms that name more organisms than codes
or carry a deposit number beside another code.
- 13 (38935259, species only): CLOSED, the exclusion is right; its lost results are listed
  under "Evidence lost because the product was not named" in the screening report.
- 30 (41291801, maker Morepen) and 37 (40740643, 41094655, 41002774, 40871692, 40717466;
  40793826 kept for its registered product name): CLOSED, a maker is not a brand (rule 3).
- 53 and 60 (VSL#3, Vivomixx, Visbiome): CLOSED by the alias principle: Vivomixx and
  Visbiome are one unchanged product under two names and stay joined; VSL#3 changed maker
  in 2016, so its two records pool only with each other. vsl3 available.
- 54, piece by piece:
  - 25862297 (Ecologic Barrier recorded with eight W codes; the product has nine): OPEN,
    needs the paywalled full text; today both its results are not counted, so no row
    depends on it. not available.
  - 40722352 (GG plus an unnamed B. longum): CLOSED, excluded as not named. This removed
    three tier-C benefit rows (gg anxiety, depression and sleep, 99 people; gg is
    available).
  - 37502424 (NEXARS: four strains all tagged "GH", maker NEXARS, no product name): CLOSED
    today, excluded as not named; two tier-C null rows (anxiety, depression, 72 people)
    left with it. not available. Re-checked 25 October: the trial's protocol paper
    (PMC9686296) puts the tablet contents in a supplement and prints no strain code either.
  - 38172876 (blend under one code): CLOSED, excluded as not named.
  - 35677549 ("BI04", probably Danisco's Bl-04): KNOWN LIMIT in rule 4 (the Bl-04/BL04
    collision); the record has no counted result, so no row depends on it.
  - 30937345 (Lactoflorene Plus, three strains, four codes): CLOSED, codes and built-in
    vitamins fixed; the entity is bb12+bc513+la5+lcasei431, available.
  - lactocare (29432877, 35685534, 41457283, 41951219): OPEN for the second run; the maker
    sells several forms and no shop page was found, so the four records may not be one
    product. not available.
  - 38445822 (vitamin D in the I.31 record): CLOSED as moot; the record has no counted
    result, so nothing pools or fails to pool.
- 55 (products whose strains are unpublished): CLOSED, a property of the products.
- 44 (42041827 Part II, heat-treated arm): KNOWN LIMIT in rule 4.
- Neuralli Mood (live PS128 plus heat-treated PS23 in one arm, from the availability
  probe): KNOWN LIMIT in rule 4. ps128+ps23 available.
- 33 (faecal transplants under two codes): CLOSED, the codes are informational (rule 3)
  and the five records are consistent.

## 5. Which scores count — CLOSED by the admission test; re-reads owed
Ruling (rule 5): a score joins a list by four tests; every admission and refusal is in
`notes/score-admissions.md`; the screening report marks a note that names a score on its
own condition's list.
- 3, 7, 12, 17, 20, 21, 26, 31, 35, 40, 45, 51 and the wave-2 fix-log candidates (DASS-21
  total, GHQ-28, Stress Response Inventory, IDS/QIDS, DSSS): CLOSED, every named score is
  admitted or refused with the test it failed. Fifteen scores joined today.
- 11 (CESD-R): CLOSED, 38658619 already records the revised CES-D as `ces-d` and the
  aliases now say so; the revision keeps the 20 items and the 0–60 total.
- 67 (41286799, a Sleep Self-Report harm hidden by the list): CLOSED, the Sleep Self-Report
  and the CSHQ passed the four tests and joined the sleep list; the harm is recorded
  (between groups, week 6) and the trial now sits in the "choice of score changes the
  result" list. nourishkefir available. Known limit in rule 5: a score that fails the tests
  stays hidden either way.
- 28 (the OSA-MA has no total): CLOSED 21 September.
- 9, 22, 25, 29, 36, 46, 62 (the list order beats the trial's own primary endpoint):
  CLOSED 21 September by the user's ruling; the cost is the "Trials where the choice of
  score changes the result" list in the screening report.
- 47, 61, 63, 64, 65 (the re-read wave): CLOSED, record of done work.
- 66 and pending 32601955, 37026368, 34444980: OPEN only for a person with journal access
  (closed texts, or a supplement); nothing is guessed. ps128 (34444980) is available.
- Re-reads owed where an admitted score was named:
  - done today, first run: 42034654 PAS, 39920878 GDS, 31061952 PHES, 28101105 PSQ,
    38361371 Mullen, 36606510 ESS, 41286799 Sleep Self-Report and CSHQ.
  - blocked by unreachable full texts, first run: 31478755 PRAS-ASD (eight-strain DSM key,
    available), 36634645 POMS under felt-stress (bb077+pbs072, available).
  - second run: 39417900 PRAS-ASD, 41821785 Goldberg (both scores), 33333767 CBCL anxiety,
    32300799 GDS-K, 41599868 PROMIS depression (and whether PROMIS anxiety was reported),
    35610236 PDSS, 41535300 ASC-ASD, 39163908 CogState (re-open the refusal if it reports
    a composite).
- One false mark remains in the screening report: 33212907's note says "adapted from the
  PHQ-9" and is marked for phq-9; the questionnaire is study-made and refused. 41821785's
  "Goldberg Scale" note is marked since 25 October, when that wording became an alias.

## 6. Results that cannot be reached — CLOSED
- 6, 10, 15 (four readers asked to split `result_not_accessible`): CLOSED 21 September,
  one code with a wider definition (rule 6).
- 32 (41410576, 41502201, 41572422 pushed to `not_accessible` on a day Europe PMC
  returned HTTP 503): CLOSED as not a tooling loss after all: Europe PMC holds no full
  text for any of the three (checked 18 October), nor for 41679635, 39385735, 30234616 or
  30266270. Only journal access can open them.
- 48 (30234616, 30266270 paywalled; 39385735, 41679635 behind a bot check): OPEN for a
  person with access; the records were copied through unchanged.
- 34 (the newest papers are a quarter closed): a fact for the report, nothing to rule.

## 7. Exclusion reason codes — CLOSED as informational
Ruling (rule 3): the reason code feeds the screening report and nothing else, so a
debatable code moves no tier.
- 19 (observational studies under `not_an_intervention_study`), 38 (a retraction notice),
  59 (spot-check disagreements), 16 (a fermented-food diet as `not_a_probiotic`): CLOSED.
- 4 (38240683, a look-back at patients already given Colicron, recorded eligible and
  `single_group`): CLOSED 25 October 2026. The paper calls itself "a retrospective
  observational study" of patients treated in care, so it did not give the product; three
  cohort studies (34601846, 34806521, 34869782) were already excluded on that ground. Rule
  3's first test now names a look-back, 38240683 is `not_an_intervention_study`, and
  colicron (one tier-D anxiety row, available) left the catalogue.

## 8. Split reports — CLOSED, with a known limit
- 2 (37720373 and 38350465 are one trial; the PSQI benefit in the later paper is lost):
  KNOWN LIMIT in rule 3. bl04+lf16+lp01+lr06 is available, so the loss is on a first-run
  entity: one sleep benefit, 39 people.
- 5 (PROVIT: which paper is first): CLOSED, rule 3 says the first report of the results;
  33171595 holds the record.
- 14 (pointer chain): CLOSED, the checker refuses a pointer at a secondary report.

## 9. Harm — FOR YOUR EYE
- 43: 42041827 (cect7347+cect8361: cortisol stayed flat on the probiotic while it fell on
  placebo, interaction p = 0.039) and 42162021 (familact: DASS depression rose against a
  fall, p = 0.014) were the catalogue's first two harms; 41286799's Sleep Self-Report is
  the third. Each is what rule 6 says. The first two entities are not available.
- 42 (41561177, the agent was wrong about a within-group cortisol test): CLOSED; the
  record has since become a secondary report of 40046755.

## 10. Two results under one listed score — CLOSED 25 October 2026
- 1 (37513541, NCC3001: saliva cortisol as the awakening response, null, and as the
  response to the Maastricht Acute Stress Test, higher on the probiotic): CLOSED by a rule
  6 sentence: when a paper reports both a cortisol level and the response to a laboratory
  stress test, the level counts. The record already held the awakening response. Sweep: 57
  counted cortisol results, one paper reports both, nothing moved. ncc3001 not available.

## 11. Two schedules of one product — CLOSED 21 September
- 58 (40175540): CLOSED, rule 4 says two schedules are one arm.

## 12. Record of done work — CLOSED
- 23, 24 (fixes of the day), 52 (aliases), 56, 57 (the spot check): CLOSED.

## What is still open, in one place
First run (the entity is on the available page):
- 31478755 and 36634645: re-read for PRAS-ASD and POMS once a full text can be reached
  (Europe PMC still returned HTTP 500 for both on 25 October).
- 37720373 / 38350465: the lost PSQI benefit is a known limit; say if split reports
  should be handled differently.

Second run:
- lactocare: four records, one product or several.
- 25862297: the ninth W code, paywalled.
- The eight second-run re-reads for admitted scores (class 5).
- 32601955, 37026368, 34444980, 30234616, 30266270, 39385735, 41679635, 41410576,
  41502201, 41572422: journal access only.

Nothing on this list needs a ruling from the user; every item waits on a text or a shop.

Known limits, written in RULES.md: the two-analysis-sets sweep (rule 6); Bl-04/BL04
(rule 4); a mixed live and heat-treated arm (rule 4); a two-part trial (rule 4); split
reports (rule 3); unanswered record-condition pairs (rule 2); a score that fails the four
tests stays hidden (rule 5).
