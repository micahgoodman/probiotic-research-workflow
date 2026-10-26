# Status check, 18 October 2026 (night), re-checked 25 October 2026

## Where things stand
- 1,117 records, every paper on every search list; validate 0 errors; 89 tests OK, none skipped.
- Tiers: 46 B, 216 C, 51 D rows (313 rows over 151 entities). 111 rows are on the "Available to
  buy today" page; 41 of 151 entities have a product page. (Numbers of 25 October 2026; the
  18 October night build was 46/216/52, 314 rows, 152 entities, 112 available rows.)
- Before today's rulings (the morning build): 43 B, 226 C, 51 D, 320 rows over 154 entities,
  112 available rows.
- Nine rulings were written into RULES.md today, each dry-run on the records first: a shared
  registration number is listed, never refused (rule 3); a result for a condition no search
  asked about counts (rule 2); "everyone who joined" means intention to treat (rule 6); "the
  end of the treatment period" is the trial's stated endpoint (rule 6); a blend is named
  only when every strain is named, a brand is a sale name, and exclusion codes are
  informational (rule 3); a brand or a second code joins its codes by alias with a source
  (rule 4); a score joins a list by four tests, and the screening report marks a note that
  names a score on its own condition's list (rule 5).
- Fifteen scores joined the lists (notes/score-admissions.md). Seventeen record changes:
  four blends excluded as not named (40722352, 42255712, 38172876, 37502424); 42059569
  restored; twelve records edited (30937345, 37720373, 33545934, 39798036, 40583505,
  42034654, 39920878, 31061952, 28101105, 38361371, 36606510, 41286799).
- Three aliases added with sources (dsm23233 to bl04; kabp023 to cect7485; kabp052 to
  cect7480; notes/alias-sources/probiotical-ab-biotics.md). available.json is edited
  directly now; the probe's working files are archived outside the repository.
- notes/scripts/shape-scan.py finds blends with too few codes and deposit numbers used as
  a second code; run it after any batch of record edits.

## Rows that moved today (morning build to night build)
- Removed: gg anxiety, depression and sleep (C benefit, 99 people, available) with
  40722352; gh+prebiotics anxiety and depression (C null, 72 people) with 37502424; the
  four dsm23233+lf16+lp01+lr06 rows (merged by alias into bl04+lf16+lp01+lr06);
  fructooligosaccharides+gbi30 felt-stress and the bb12+...+zinc cortisol row (re-keyed).
- Added: 299v felt-stress C null; bb12+bc513+la5+lcasei431 cortisol C null;
  bl04+lf16+lp01+lr06 felt-stress C null; cect7480+cect7485+vitamind sleep C null;
  lactibiane sleep D benefit.
- Changed: 299v cortisol C benefit to D null (28101105's day-10 win is not the endpoint
  figure); bl04+lf16+lp01+lr06 anxiety and cortisol C to B "mixed, 1 of 2", depression D
  to B "no difference in both"; lactofem depression D one study to D "benefit in both of 2
  weaker studies" (352 people); r0052+r0175 depression B 3 of 6 to 4 of 7; the W-key
  anxiety B null in 3 to null in 4; the eight-strain DSM key cognition D null to D "mixed,
  1 of 2 weaker".

## Open items
The one list is notes/open-questions.md, section "What is still open, in one place". As of
25 October 2026 nothing on it needs a ruling from the user.
- First run: 31478755 and 36634645 re-reads blocked by unreachable full texts; the
  split-report loss on 37720373 (a known limit unless the user wants split reports handled
  differently).
- Second run: the four lactocare records; 25862297's ninth W code; eight re-reads for
  admitted scores; ten papers that need journal access.
- Known limits are written in RULES.md and listed at the end of open-questions.md.
- Dropped from the list: the sample of main_endpoint "no" records. main_endpoint decides
  nothing the program computes (September item 46), so the sample would buy nothing.

## Re-check of 25 October 2026
Every judgement call of 18 October was read again against its source. All stood: 40722352
names no code and no brand for its B. longum; 37502424's protocol paper prints no code
either; 37720373's BDI has "no between-group differences at any of the five time points";
28101105 tests cortisol between groups at day 10 only and prints no day-14 test. Two open
items were then ruled and applied: a look-back is not an intervention study (38240683
excluded; colicron, one tier-D row, left the catalogue and `available.json`), and a cortisol
level beats a stress-test response (37513541 unchanged; sweep of 57 cortisol results moved
nothing). Small fixes: the shape scan skips aliased deposit numbers and arms made only of
deposit numbers (false positives gone; two true two-strain hits remain); "Goldberg Scale"
became an alias so 41821785 is marked. Europe PMC still returns HTTP 500 for the two blocked
full texts. The open list in notes/open-questions.md now holds nothing that needs a ruling.
