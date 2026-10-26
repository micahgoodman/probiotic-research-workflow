# Probiotic Evidence Catalogue, version 2: the rules

**Status: design approved by the maintainer, 20 September 2026. Every one of the 1,117 papers the searches found has a record (21 September 2026). Rule 8, the availability split, was added on 18 October 2026 and every entity has its availability entry (same day). Also on 18 October 2026 the open questions of September were closed by class: nine rulings, fifteen admitted scores and seventeen record changes, listed under "Decisions of 18 October 2026" at the end and tracked in `notes/open-questions.md`. A re-check on 25 October 2026 added two rulings and one record change ("Decisions of 25 October 2026").**

This catalogue answers one question: for six mental-health conditions, which probiotics were
tested in people, how strong is that evidence, and what did the studies find?

Every rule below is mechanical. A rule is mechanical when two people who read the same paper
must write the same record. People record facts about each paper. A program computes every
tier and every verdict from those facts, and no rule has an exception. When a paper does not
fit a rule, the record says why with one fixed code. Nobody downgrades, weighs or argues in
prose.

## Why version 1 was stopped

Version 1 needed too many judgment calls, and five causes produced almost all of them.
Version 1 is kept offline by the maintainer. An early snapshot of it, with one strain
researched, is this repository's first commit (9 August 2026).

| Cause in version 1 | The numbers | The rule that removes it |
|---|---|---|
| People typed the tier, then argued exceptions | 740 of 1,149 human rows rested on one trial; one tier ruling moved about 190 rows | Rules 5, 6 and 7 |
| We recorded everything about each strain | 108 outcome ids; 34% of rows were animal or lab rows | Rule 1 |
| We tried to prove that nothing exists | `searched_empty`, pass debt, 4,500 characters of `gaps` per file | Rule 2 |
| People typed fields a program can compute | tier, rationale, consistency, `pass_summary`, `known_for` all drifted | Rule 7 |
| We decided what "the thing tested" was | product or strain, co-ingredients, yogurt starters | Rule 4 |

## Rule 1. There are six conditions and nothing else

The conditions are felt stress, cortisol level, anxiety, sleep, depression and cognition.
They are listed in `conditions.json`. Animal studies, lab studies, mechanisms, other blood
markers and safety rows are out.

Felt stress and cortisol are two separate conditions that never mix (user decision,
20 September 2026). Felt stress is what a person reports on a questionnaire. Cortisol is a
hormone level. For cortisol, a lower level is counted as a benefit.

People with a diagnosis and people without one are pooled (user decision, 20 September 2026).
Each trial record keeps a short `population` note for the reader, but the note never changes
a count.

## Rule 2. Trials are found by one fixed search for each condition

`tools/search.py` runs one PubMed search for each condition and saves the list of papers
in `search/`. The search words are in `conditions.json`. On 20 September 2026 the six
searches returned 1,117 different papers.

Every paper on a saved list must get a record. That is how the catalogue proves it is
complete: the checker fails if any paper on a list has no record. There is no other record
of "we looked and found nothing".

A paper that is not on a saved list cannot be recorded. This keeps strain inclusion free of
choices. **Known limit:** a trial whose abstract never mentions the condition cannot be found
this way. A test against version 1 found 64 of 72 known trials, so about 1 trial in 9 is
missed. The missed trials measured mood as a side measure only. If you later want to add
papers by hand, add a list file to `search/` that names them; no code changes.

**A result for a condition whose search did not find the paper counts the same** (ruled
18 October 2026). The searches decide which papers get a record, not which facts in a
record count: a paper the sleep search found that also reports a depression score gives a
depression result. Dry run before the ruling: 39 such results on 37 records, 37 of them
counted; dropping them would have changed 31 rows, emptied 25 and moved 5 entities from
tier B to C. **Known limit:** each search asks a paper about one condition, so most
records answer one condition only (154 of the 338 eligible records answer a single
condition, and 1,352 of the 2,028 paper-and-condition pairs have no answer). A result for
a condition no search asked about is recorded when a reader notices it, not by any rule,
so the catalogue undercounts such results.

### The pre-screen writes the easy exclusions by program

PubMed labels some papers as a review, a systematic review, a meta-analysis, a correction
notice, a comment, an editorial or a guideline. None of those report people of their own,
so none can hold a trial result. `tools/prescreen.py` writes the
`not_an_intervention_study` record for them, so that nobody has to read them.

The test is deliberately one-sided, because nobody reads a cleared paper again. A paper is
cleared only when PubMed gives it a label from the cleared list **and never** gives it a
label that means a study, such as "Randomized Controlled Trial", "Clinical Trial",
"Observational Study" or "Case Reports". A study label always wins, because PubMed sometimes
labels a real trial "Review" by mistake. A paper with no labels at all is never cleared.

On 20 September 2026 the pre-screen cleared 296 of the 1,117 papers, and 821 were left to
read. Twenty of the cleared papers were checked by hand: all twenty were reviews,
meta-analyses or a correction notice.

## Rule 3. A paper is eligible only if it passes every test below

A paper is recorded as `eligible`, or as `excluded` with one reason code.

| Test | Reason code when it fails |
|---|---|
| It reports a study that gave the product, not a review, a plan for a study, a comment, a correction, a survey of what people eat, or a look back at people treated outside the study | `not_an_intervention_study` |
| The thing given was live or non-viable bacteria or yeast (a fibre, a food or a medicine on its own is not) | `not_a_probiotic` |
| The paper has not been retracted | `retracted` |
| The study was in humans | `not_human` |
| The product was swallowed (food, drink, capsule, powder) | `not_oral` |
| The paper names a strain code or a brand | `entity_not_named` |
| It is the first report of this trial | `secondary_report` (and `of_pmid` names the first report) |
| It measured at least one of the six conditions | `no_listed_condition` |
| The abstract or a free full text can be read | `not_accessible` |

Never bypass a paywall or a CAPTCHA. A paper that cannot be read is `not_accessible`.

**The tests are applied in the order of the table, and the first failure wins.** This stops
two researchers giving the same paper two different, equally true, reason codes.

**The first report of a trial usually has no record of its own.** A follow-up paper often
reports the mood results of a trial whose first paper was about something else, so the six
searches never returned it. `of_pmid` still names that paper, but the checker asks for a
record only when we hold one. When we do hold it and it was excluded, that is an error,
because the trial would then be counted no times at all.

**`entity_not_named` needs the full text.** When the abstract names no strain code and no
brand, and the full text cannot be read, the reason is `not_accessible`, not
`entity_not_named`. The catalogue must not say "this paper named no strain" when nobody has
looked in the Methods. This came out of the pilot of 20 September 2026, where three closed
papers were nearly recorded as naming no strain.

**A blend is named only when every strain in it is named.** The naming test asks whether
a reader could buy what was tested. "L. rhamnosus GG and Bifidobacterium longum" names one
strain and leaves the other to guesswork, so without a brand it fails the test. Recording
it under the one named strain would count a two-strain blend as a trial of that strain,
which rule 4 forbids. (Ruled 18 October 2026. Backward sweep by
`notes/scripts/shape-scan.py`, which lists every arm whose stated entity names more
organisms than it has codes: PMIDs 40722352, 42255712 and 38172876 moved to
`entity_not_named`, and 40722352 took three benefit results away from GG.)

**A brand is the name a product is sold under**: a trade name, or a registered generic
product name printed on the box, such as China's "Live Combined Bifidobacterium and
Lactobacillus Tablets" (PMID 40793826). A maker's name, an approval number or a species
list written by the authors is not a brand. (Ruled 18 October 2026.)

**The reason code on an excluded paper feeds the screening report and nothing else.** No
code changes a count, so a code that names the wrong row of the table is fixed when
somebody sees it, and nobody re-reads excluded papers to check their codes. (Ruled
18 October 2026.)

A weak design is not a reason to exclude (user decision, 20 September 2026). Early evidence
is kept and gets the lowest tier. Each eligible record states its `design`:

| `design` | Meaning |
|---|---|
| `randomized_placebo` | People were put into groups by chance, and one group took a dummy: the same food, drink or capsule without the bacteria |
| `randomized_other_control` | Groups by chance, but the other group took nothing or took another treatment |
| `not_randomized` | There was a second group, but people were not put into groups by chance |
| `single_group` | Everyone took the probiotic |

### Three words that caused disagreements in wave 1

**A control that is the same thing without the bacteria is a placebo**, whatever the paper
calls it. Plain milk against the same milk fermented with the strain is `randomized_placebo`.
A control formula that is the same formula without the strain is `randomized_placebo`. Use
`randomized_other_control` only when the other group took something genuinely different: no
treatment at all, a different medicine, or a diet. Nutrition papers often avoid the word
"placebo", and that one word decides whether a trial can ever reach tier B or C.

**"Measured one of the six conditions" means measured at all**, not measured with a listed
score. A trial that measured sleep with its own diary is eligible, and its sleep result is
`not_counted` with the reason `instrument_not_listed`. That is how `build/screening.md`
learns which scores are common enough to add. `no_listed_condition` is only for a paper that
measured none of the six at all.

**"The first report of this trial" means the first report of its results.** A protocol, a
plan or a registration entry is not a report of results, so the paper that first gives the
results is the first report, even when a protocol was published years earlier.

**A secondary report points at the trial's own record, never at another follow-up paper.**
When the paper you are pointing at is itself a `secondary_report`, point at what *it*
points at instead. A chain of pointers hides the trial's record and makes the screening
report announce a loss that never happened. The checker refuses a chain.

**Known limit:** when one trial's results are split across two papers (PMID 37720373
holds anxiety, depression and cortisol; PMID 38350465, the same trial's sleep paper, is
its `secondary_report`), the second paper's result is lost. One record per trial is the
rule; a code for "a second report with a new condition" would be written only if a second
case appears.

**One registration number can cover more than one trial, so a shared number is never an
error.** A hospital may register a programme once and then run it in several diseases
(PMIDs 34835954 and 38361371, PS128 in Tourette syndrome and in Rett syndrome, share
NCT03259971), or run one programme in women and then in men (PMIDs 38216917 and 42059569
share IRCT20160524028038N14). Whether two papers are one trial is read from the papers: a
paper that reports a trial already reported is `secondary_report`, and nothing else makes
it one. Write each paper's registration exactly as that paper prints it, and never edit a
number to dodge a collision. `build/screening.md` lists every number that sits on more
than one eligible record, so a reader can look. (Ruled 21 September 2026. The checker's
refusal of shared numbers was removed on 18 October 2026: over four weeks and 193
registered records it caught no double count, and it kept PMID 42059569, a 240-person
trial, out of the catalogue for 27 days as a "duplicate" of a 112-person trial in
different people.)

**A faecal transplant taken by mouth is `entity_not_named`.** Donor stool is live
bacteria, so it passes the probiotic test, and it then fails the naming test, because
donor microbiota has no strain code and no brand by its very nature. Whether the full
text can be read makes no difference here. A transplant given by colonoscopy or enema
fails earlier, on `not_oral`. (Ruled 21 September 2026, after five papers were split
between two codes.)

**`result_not_accessible` covers both kinds of unreachable result.** Use it when the paper
does not say whether the change was significant, *and* when the paper says a score moved
but never names which score it used. Both mean the same thing for a reader: the result
cannot be checked. (Ruled 21 September 2026. Four researchers proposed splitting this code
in two; the maintainer chose to keep one code rather than add machinery.)

### How to count the people

`n_randomized` is the number of people the paper says were put into groups, before anybody
dropped out. When the paper gives only the number who finished, or only the number whose
results were analysed, use that number. When the paper gives no number at all, use `null`,
never `0`. This number is shown to readers and never changes a tier.

## Rule 4. The entity is the difference between the two groups

The thing tested is whatever the probiotic group took and the other group did not. In a
study with one group, it is whatever that group took. If that
is one strain, the entity is the strain. If it is a blend, the entity is the blend. If it is
a strain plus vitamin B6, the entity is "the strain plus vitamin B6". We never split a blend
into its strains, and we never ask whether a co-ingredient "could explain" the result.

Two trials test the same entity only when their entity keys are equal. `tools/catalogue.py`
computes the key from `strain_codes` (or `brand` when no code is given), `other_actives`
and `preparation`. A heat-killed preparation is a different entity from the live one.
Spelling variants ("PS 128", "PS128") are joined by `aliases.json`, which is a lookup table
and nothing more.

**An ingredient that is part of the product itself is not an added active** (user decision,
21 September 2026). Many products are sold with a prebiotic or a vitamin already inside them.
`other_actives` holds only what the trial added on top of the product. Listing a product's own
ingredients again splits one product into several entities: Familact appeared under four keys,
and SIM01 and Pedilact under two each, purely because some papers named the built-in prebiotic
and others did not. Backward sweep, worked the same day: the built-in ingredient was removed
from PMIDs 36745650, 34466612, 38071990, 35968208 and 35769391, which pooled the three
Familact records into one entity. The sweep covers only products a source could settle; a
record whose product nobody has looked up may still carry this fault.

**The vehicle and the coating never change the entity** (user decision, 21 September 2026).
A yoghurt and a capsule of one strain are one entity, and so are a coated and an uncoated
capsule of one product. Backward sweep: PMID 27178566 tested a dual-coated and a non-coated
Duolac Care, and both arms now carry one entity name.

**The dose belongs in `dose_as_stated` and nowhere else.** An ingredient written as "inulin
15 g" makes its own entity key and can never pool with plain "inulin". Backward sweep:
PMIDs 30217229, 31379269, 32589828, 32601955, 33593462 and 33641656 were corrected.

**Two schedules of one product are still one arm.** A trial may give the same product on
two timetables, such as one group starting before birth and one after, against a single
control group. The timetable is not part of what a shopper buys, so both groups are the
same entity and the record holds one arm. User ruling of 21 September 2026. The backward
sweep looked for every record that mentions a split timetable, and for every record whose
arms build the same entity key twice. It found one paper of the first kind, PMID 40175540,
which was already recorded this way, and one of the second kind, PMID 27178566, whose two
vehicle arms were merged. The checker now refuses two arms that mean one entity, so this
cannot come back silently.

**A brand or a second code joins its strain codes by alias when a source publishes the
join and the product has not changed.** Vivomixx and Visbiome are two market names for one
maker's one product with eight published DSM codes, so `aliases.json` sends both names to
the DSM key (`notes/alias-sources/desimone.md`). A strain printed under two codes is the
same case: PMID 37720373 prints "Bifidobacterium longum 04 (DSM 23233)" and PMID 40077722
prints "BL04", and the maker's patent and the product page give both names for one strain,
so `dsm23233` is an alias of `bl04` and the records pool
(`notes/alias-sources/probiotical-ab-biotics.md`). The join lives in the alias table with
its source; nobody writes a code into a record that the paper does not print. VSL#3 is the
case that fails the test: after the 2016 split, the product sold as VSL#3 is made by a
different manufacturer from the original formulation, so its trials are not all trials of
one thing, and the two VSL#3 records (PMIDs 25092036 and 34681287) pool only with each
other. (Ruled 21 September 2026 for VSL#3, with a sweep of every record naming VSL#3,
Vivomixx, Visbiome or the De Simone Formulation; 18 October 2026 for the alias principle.)

**Known limits (18 October 2026).** The key keeps letters and digits only, so IFF's
*B. lactis* Bl-04 and Probiotical's *B. longum* BL04 share the code `bl04`; today they sit
in different blends (PMID 37497057's six-strain product and the four-strain Probiotical
product), so no row merges, and a single-strain trial of either would need a rule. A
product that mixes a live strain with a heat-treated one (Neuralli Mood, PMID 41464897:
live PS128 plus heat-treated PS23) has one arm and one preparation, `live`, so its key
does not say that part of it was heat-treated. A trial in two parts, where the second part
re-randomises the first part's placebo non-responders onto a different preparation
(PMID 42041827, Part II, heat-treated), holds the first part only; the second is not a
parallel trial against placebo. Each is one record; a second case would be the time to
write a rule.

When one trial tested several doses of the same entity, record the highest dose only.

## Rule 5. One score per condition, picked by the program from a fixed ranking

Each condition has a ranked list of accepted scores in `conditions.json`. The score for a
trial is the highest-ranked score that the paper reports. Only the exact score named on the
list counts: a total score where the list says total, and never a part of it.

The lists are ranked the same way for every condition: a score rated by a clinician comes
first, a questionnaire made for that one condition comes next, and a part of a mixed
questionnaire comes last.

**When a paper reports two or more listed scores for the same condition, record every one
of them, each with its own result. The program picks the one nearest the top of the list.**
The researcher never picks (user decision, 21 September 2026). The ranking exists for
exactly this case: in the pilot of 20 September 2026 one paper reported both HADS-D and the
DASS-21 depression score, and two researchers picked different ones.

Until 21 September 2026 the researcher picked the score and the other was thrown away. That
hid the cost of the ranking. PMID 39741947 reported HADS-A (benefit) and Zung SAS (no
difference), and only the Zung result was saved. With every score in the record, the rule
lives in one function (`reported_scores` in `tools/catalogue.py`), a change to the rule or
to a list needs no paper to be read again, and `build/screening.md` names every trial where
the pick changes the result.

**The list always wins, even against the trial's own primary endpoint** (user decision,
21 September 2026). A paper that calls one score its primary endpoint does not thereby move
that score up the list. This was asked with the answer computed both ways over all 1,117
papers: letting the stated primary endpoint win would have changed exactly one verdict
(YRC3780 for depression, from no difference to benefit) and reworded six others. The list
was kept because every trial must be judged on the same score, whether or not its authors
named a primary endpoint. The cost is real and is printed for each affected trial in
`build/screening.md`; PMID 40603475's own primary endpoint, a POMS total benefit, is the
clearest case.

**A score with no total score can still be a listed score** (user decision, 21 September
2026). The OSA-MA sleep inventory has five factor scores and no total. It is on the sleep
list, and a paper that reports one verdict for the whole inventory gets an `osa-ma` result.
Only its individual factors are `subscale_only`. The labels in `conditions.json` say "total
score" or "global score" wherever a total is required, so the label is the test; where the
label names the instrument alone, the instrument is the score.

**A validated short form counts as the score it is a short form of** (user decision,
20 September 2026). The short form's name is written into that score's `aliases` in
`conditions.json`, so the choice is on the list and not in anyone's head. A short form is
not the same as a *part* of a score: a subscale is still `subscale_only`.

**The lists carry child scores as well as adult ones** (user decision, 20 September 2026).
Sleep has the Sleep Disturbance Scale for Children; cognition has Bayley-III and WPPSI. A
child trial's result counts the same as an adult one, in the same way that people with a
diagnosis and healthy people are already pooled.

### When a score joins a list (ruled 18 October 2026)

A score is admitted to a list when it passes all four tests, and refused when it fails
any one of them. The tests, in order:

1. It is a named instrument that was published and validated before the trial. A diary, a
   visual analogue scale, a single item, a single task or a battery with no overall score,
   a physiological signal and an adverse-event count all fail here.
2. It was built to measure that condition, or it is a named part of a validated
   mental-health questionnaire that measures it. A domain or an item of a quality-of-life
   or disease questionnaire fails here.
3. It gives one total or global score, or one whole-instrument verdict, that measures the
   condition alone. A combined anxiety-and-depression total fails here.
4. At least one eligible record reports it. A score nobody has reported is not listed,
   however good it is.

An admitted score is placed by the class rule above (clinician-rated, then made for the
condition, then a part of a mixed questionnaire). Every admission and every refusal, with
the test it failed, is in `notes/score-admissions.md`. The first pass over the 152
unlisted notes (18 October 2026) admitted thirteen scores and refused the rest; two child
sleep questionnaires were admitted the same day from a reader's report of a hidden harm.

A note that names a score already on its condition's list is a record to read again, not
a list to extend. `build/screening.md` marks every such note so finding them is no longer a
reading job. Only the condition's own list is checked: matching every list gave three
permanent false marks (a depression scale's domains used for anxiety and sleep; a cognition
score whose abbreviation is also a depression score's) and no true one.

**Known limit:** an unlisted score hides results in both directions. In PMID 41286799 the
Sleep Self-Report found more sleep problems on the kefir (p = 0.02) while the record showed
a null from the listed actigraphy score. That questionnaire passed the four tests and joined
the sleep list on 18 October 2026, so the trial now appears in the screening report's list
of trials where the choice of score changes the result. A score that fails the tests stays
hidden either way, and the report's list of unlisted scores is the only place to see it.

**The score must be measured in the people who took part.** A score measured in a parent, a
carer or a partner is `not_measured` for that trial, even when the paper reports it as an
outcome. The catalogue says what the probiotic did for the people who took it.

| Situation | Reason code |
|---|---|
| The condition was not measured in this trial | `not_measured` |
| The paper used a score that is not on the list | `instrument_not_listed` (and `instrument_as_stated` names it) |
| Only a part of a listed score is reported | `subscale_only` |
| Only a subgroup result is reported | `subgroup_only` |
| The score was measured, but the abstract or a free full text does not say whether the change was significant | `result_not_accessible` |

`build/screening.md` counts every code and lists the most common unlisted scores. That is
how we learn that a ranking list needs one more entry.

## Rule 6. A result is one of three words, and the record says what was compared

Use the result at the end of the treatment period, for everyone who joined the study.

**"Everyone who joined" means the analysis of everyone who was put into a group**
(intention to treat). When the paper reports both that analysis and a smaller one
(completers, per protocol, modified intention to treat), the full-set result decides:
PMID 35654766's between-group effect is significant only in the modified set, so its
record says `no_difference`. When the paper reports only a smaller set, that result
counts, because it is the only result there is; the record does not say which set it came
from. When the paper shows it ran the full-set analysis but prints only the smaller set's
figure for a score, that score is `result_not_accessible` (PMID 40583505: the K-MoCA
improved "in the per-protocol group", and the full-set figure is behind a paywall).
(Ruled 18 October 2026.) **Known limit:** the backward sweep over the 338 eligible
records, for papers that report two analysis sets, has not been worked; it cannot be found
by grep, and 38892634 is the only other record known to have been checked this way.

**"The end of the treatment period" is the trial's own stated endpoint.** A between-group
difference at an earlier time point, with no readable figure at the endpoint, is
`result_not_accessible`, because taking the one time point that worked out of several
would be cherry-picking. Applied to PMIDs 41679635 and 26419583 (21 September 2026) and
28101105 (18 October 2026); written here on 18 October 2026 after the third case.

**When a paper reports both a cortisol level and the cortisol response to a laboratory
stress test, the level counts.** The level is a resting or awakening sample at the stated
endpoint. The change during a Trier, Maastricht or cold-pressor test is a reactivity
measure, a different quantity, and it does not replace the level. PMID 37513541 reports
both: the awakening response (null) is the record, and the higher post-test response on the
probiotic is not. Sweep (25 October 2026): of 57 counted cortisol results, 37513541 is the
only record that reports both; 32687924 measures cortisol only around its stress test and
keeps its null as that trial's only cortisol level. (Ruled 25 October 2026.)

- `benefit`: the paper says the probiotic group did better, and the difference was
  statistically significant.
- `no_difference`: the paper says there was no significant difference.
- `harm`: the paper says the probiotic group did worse, and the difference was significant.

Each result also states its `comparison`:

| `comparison` | Meaning |
|---|---|
| `between_groups` | The probiotic group was compared with the other group |
| `within_group` | The probiotic group was compared with its own start ("improved from baseline") |
| `not_stated` | The paper gives a result but does not say which of the two it is |

`between_groups` needs a reported comparison between the groups: a p-value, a difference
with a range of uncertainty, or a plain sentence saying the groups were or were not
different on that score. **A sentence saying the groups were "comparable" or "similar", with
no test behind it anywhere in the paper, is not such a comparison.** In that case record the
within-group result the paper does report, with `comparison: "within_group"`. This came out
of the pilot of 20 September 2026, where the choice turned one paper's benefit into a null.

When a paper gives both kinds of result for the same score, record the `between_groups`
result and ignore the other. A trial that found no difference against placebo is a null,
even if both groups improved from their start.

Reading a change inside one group as a win against placebo was the most common real error
in version 1. Version 2 records such a result honestly, and rule 7 keeps it in the lowest
tier. Each record also says whether the score was the study's main endpoint: `yes`, `no` or
`not_stated`. **`yes` and `no` need the paper's own words** — "primary endpoint", "primary
outcome", "main outcome" or the same idea said plainly. A paper that states an aim but names
no primary endpoint gets `not_stated` for every score. Guessing from the title or the aim
was a disagreement in the pilot of 20 September 2026. **A score the paper calls a "secondary
endpoint" or "secondary outcome" is `no`** (user decision, 21 September 2026): "secondary" is
the plain-words opposite of primary, so the paper has said it. The flag is kept for the reader
and for later rule changes; it never decides which score speaks for a trial. (This sentence
lived only in the reading brief until 18 October 2026; the backward sweep over the
`not_stated` values it may change has not been worked, and it moves no verdict.)

## Rule 7. The program writes every tier and every verdict

People record studies. `tools/build.py` does everything else: it groups results by entity
and condition, counts them, and writes the tier and the verdict.

A **trial result** is a `between_groups` result from a `randomized_placebo` study. Every
other result is a **weaker result**.

| Tier | The rule |
|---|---|
| **B** | Two or more trial results |
| **C** | Exactly one trial result |
| **D** | No trial result, and one or more weaker results |

The tier has no exceptions (user decision, 20 September 2026). It never moves for the size
of a trial, for who paid for it, or for a side endpoint. Those facts are shown beside the
tier. Weaker results never lift a tier: one trial plus three weaker studies is still C, and
the weaker studies are shown in their own column. The number two is one constant in
`tools/catalogue.py`.

This replaces the version 1 ruling "reported direction, one tier down" for a result with an
unstated comparator. Such a result keeps its direction and sits in tier D.

Tier A (a review that pools one strain's trials) is not used. Version 1 found one such case
for these conditions. Tier P (animal and lab studies) is not used. It would add about 1,775
papers, and mouse studies use tests such as the forced swim test that are not on the score
lists, so every paper would need a judgment call.

The verdict comes from the trial results for tiers B and C, and from the weaker results for
tier D.

| Results | Verdict |
|---|---|
| Any found harm | "harm in H of K trials" |
| All found benefit | "benefit in all K trials" |
| None found benefit | "no difference found in all K trials" |
| Some found benefit | "mixed: benefit in B of K trials" |

The words are "no difference found", because a trial that finds no difference has not
shown that there is none. For tier D the words "weaker studies" replace "trials". The page
also lists each study's result with its own size, for example "benefit (120 people); no
difference found (24 people)", so a reader can tell a small null from a large one. This is a count of studies. It does
not weigh them, which follows the maintainer's ruling of 20 September 2026 in version 1 ("tier B
counts trials; it does not weigh them"). A small trial that found nothing counts the same as
a large one, so the number of people is always shown beside the verdict.

## Rule 8. The catalogue is printed in two parts: what a reader can buy today, and the rest

(user decision, 18 October 2026)

**The catalogue exists for a reader who wants to act on it, and most readers act by buying
something.** So the build writes every row on one of two pages: entities a reader can buy
today, and entities nobody can buy yet. The evidence rules are the same on both pages. Only
the page is different. The first research run is the first page; the second page is worked
later.

**An entity is available when one consumer product page shows it for sale.** The page must
let a person order the product (it shows a price or a way to buy) without a prescription, and
it must name the entity: every strain code in the entity's key, or the brand when the key is a
brand. For a heat-killed entity the page must also say the organisms are heat-killed (shops
also write "postbiotic", "paraprobiotic", "heat-treated", "tyndallized", "inactivated" or
"sterilized", and in Japanese 殺菌 or 死菌; user decision, 18 October 2026, when the only CP2305 page
said 殺菌乳酸菌末, "sterilized lactic-acid-bacteria powder". Backward sweep: `cp2305+heatkilled` was
the only heat-killed entity with a found page, and it stays found). A page from any country counts, and the record
says which country (user decision: the page itself tells the reader where it is sold, and
version 1 went wrong by ranking countries). A blend that contains a strain does not make the
bare strain available: the entity is what the trial tested, and a different product is a
different entity (rule 4). **Only the strains are tested** (user decision, 18 October 2026): the page
must name every strain in the key and no other strain, and non-strain extras (vitamins,
minerals, herbs, honey, fibre) are ignored in both directions, whether the shop added them or
the trial did. A reader can take a vitamin or leave out the honey, but can get the strain
nowhere else; rule 4 still keeps the trial's combination as its own entity for the evidence.
Backward sweep over the 154 entries of 18 October 2026: two entries moved from none found to
found (`heal9`, Probi Sense with minerals; `exobdnf`, anatis with herbs); no found entry moved.

**The fact is one entry per entity key in `available.json`, and it carries no judgement.** An
entry that was found holds `url`, `product` (the name on the page), `country`, `checked` (the
date) and `names` (the words on the page that name the strain code or brand, copied). An
entity nobody could find for sale holds `"url": null`, `checked`, and `searched` (a short note
of where the search looked). There is no "probably", no "discontinued" and no opinion of the
shop. A reader can follow the link or they cannot. Pages change, so the `checked` date is
printed with the row and nothing more is promised.

**Every entity with a verdict row must have an entry, and the checker fails otherwise.** This
is the same completeness proof as the saved search lists: "we looked and found nothing" is a
recorded answer, and an entity with no entry is a gap, not a "no".

**Why the test lives here and not in rule 3.** Version 1 had this test as a gate on which
entities were recorded, with a list of countries and a judgement about discontinued products.
Every change to the gate forced a sweep over everything already excluded: on 19 September
2026 the gate was widened and 22 excluded entities had to be reinstated. Here the test decides
only which page a row is printed on. It changes nothing about which papers are recorded or how
a result counts, so a change to it can never require a paper to be read again.

## File layout

| Path | What it is | Who writes it |
|---|---|---|
| `conditions.json` | the six conditions, their search words and their ranked scores | the maintainer |
| `aliases.json` | spelling variants of strain names, each with a source in `notes/alias-sources/` | the maintainer |
| `available.json` | one consumer product page for each entity, or the record that none was found (rule 8) | the readers (see `README.md`) |
| `search/<condition>.json` | the saved list of papers for a condition | `tools/search.py` |
| `trials/<pmid>.json` | one record for one paper | the readers (see `README.md`) |
| `build/` | the catalogue and the screening report | `tools/build.py` |
| `build/prescreen.json` | each paper's PubMed labels, kept so the pre-screen can be re-checked | `tools/prescreen.py` |
| `notes/` | the decision record: open questions, score admissions, alias sources, the readers' brief, status | the maintainer |

## Commands

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'   # the tests
python3 tools/validate.py                                    # check every record
python3 tools/validate.py 123 456                            # check only those papers
python3 tools/build.py                                       # check, then write build/
SSL_CERT_FILE=<ca-bundle> python3 tools/search.py            # refresh the saved lists
SSL_CERT_FILE=<ca-bundle> python3 tools/prescreen.py         # clear reviews and the like
```

## Decisions already made (20 September 2026)

- Six conditions; cortisol is separate from felt stress; diagnosed and healthy people pooled.
- Any study counts, and a fixed ranked list picks the one score.
- Tiers B, C and D are computed. Early evidence is kept as tier D. Animal and lab studies
  stay out.
- The ranked score lists in `conditions.json` are accepted as drafted. Cognition accepts
  whole-test overall scores only, so a trial that reports only single tasks does not count.
  The screening report will show which scores to add.
- Sleep stays one condition. A wrist device and a sleep lab measure sleep itself, so they
  belong with the sleep questionnaires. Cortisol is different: it is a hormone that stands in
  for stress, which is why it was split off. Questionnaires rank first, so a device result
  counts only when a trial reports no listed questionnaire.
- The catalogue counts studies and does not pool them. A meta-analysis was rejected: it needs
  numbers that abstracts often lack, it needs many judgment calls, and two or three small
  trials give a very wide margin of error. The catalogue is a map of the evidence. It shows
  where a proper meta-analysis would be worth doing.
- Records carry no quote from the paper. It was one more element to keep track of. The
  cost is that checking a record means opening the paper again.
- Version 1 is archived, not deleted.

## Decisions of 18 October 2026

- A shared registration number is listed, never refused (rule 3). A result for a condition
  no search asked about counts (rule 2). "Everyone who joined" means intention to treat
  (rule 6). A blend is named only when every strain is named; a brand is a product's sale
  name; exclusion codes feed the screening report only (rule 3). A brand or a second code
  joins its strain codes by alias, with a source (rule 4). A score joins a list by the
  four-test admission rule, and a note naming a listed score is marked for re-reading
  (rule 5). "The end of the treatment period" is the trial's own stated endpoint (rule 6).
  Each ruling was dry-run on the records before it was written.
- Fifteen scores joined the lists (`notes/score-admissions.md`). The screening mark checks
  the condition's own list only. Four blends recorded under too few codes were excluded as
  not named (40722352, 42255712, 38172876, 37502424); 42059569 was restored; the other
  record changes are listed in `notes/STATUS.md`.

## Decisions of 25 October 2026

- A look back at people treated outside the study is not an intervention study (rule 3,
  first test): PMID 38240683, a retrospective Colicron series, is excluded, and colicron
  leaves the catalogue until a trial of it is found. When a paper reports both a cortisol
  level and the response to a laboratory stress test, the level counts (rule 6). Both were
  dry-run: the first moves one tier-D row, the second moves nothing.
