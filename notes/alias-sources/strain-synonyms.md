# strain-synonyms — strain codes that name one organism under two labels (21 September 2026)

How `aliases.json` is applied (checked in `tools/catalogue.py`, `entity_key`): the lookup runs
**per strain code first** (`canon(_norm(n))` for every name and every other_active), and then once
more on the joined key. So a per-part alias such as `rosell52 -> r0052` is legal and it rewrites
every key that contains that part, blends included. Several entries below are per-part aliases that
join no two whole keys today but keep the catalogue honest.

## Joins I am confident about

- rosell52  ->  r0052   (the surviving key is r0052; per-part alias. Rosell-52 and R0052 are one
  strain, deposited as CNCM I-1722. With the Rosell-175 alias below this turns
  `rosell175+rosell52` (4 records) into `r0052+r0175` (8 records) = 12 records for one product.)
  Source: "Lactobacillus helveticus Rosell®-52 (R0052) is deposited under number I-1722 at the
  Pasteur Institute, in the Collection Nationale de Cultures de Microorganismes (CNCM)" —
  https://www.fda.gov/media/122558/download (GRAS notice 758, "Lactobacillus helveticus R0052").
  Second source, same deposit under the older species name: "Lactobacillus acidophilus R-52,
  produced by Lallemand ... deposited at CNCM strain bank of Institut Pasteur with code I-1722" —
  https://www.cofamispa.it/en/prodotti/lactobacillus-helveticus-rosell-52-2/

  **The L. acidophilus / L. helveticus difference is a species reclassification, not two strains.**
  PMID 19083380 calls it "Lactobacillus acidophilus Rosell-52"; that is the pre-reclassification
  name for the same organism.
  Source: "Lactobacillus acidophilus Rosell-52, recently reclassified as Lactobacillus helveticus
  Rosell-52" — https://www.optibacprobiotics.com/professionals/probiotics-database/strains/lactobacillus-acidophilus-rosell-52
  Source: "The name of this species, result of a reclassification from previous denomination
  L. acidophilus, refers to the ancient name of Swiss territory (Helvetia)" —
  https://www.cofamispa.it/en/prodotti/lactobacillus-helveticus-rosell-52-2/

- rosell175  ->  r0175   (the surviving key is r0175; per-part alias. One strain, CNCM I-3470.)
  Source: "B. longum R-175, originally isolated from dairy products, is produced by Lallemand, and
  deposited in the CNCM strain bank with code I-3470" —
  https://www.cofamispa.it/en/prodotti/bifidobacterium-longum-rosell-175-2/

- cerebiome  ->  r0052+r0175   (the surviving key is r0052+r0175, because that is the composition.
  Cerebiome is a brand name for exactly this two-strain pair, previously sold as Probio'Stick.)
  Source: "Lallemand Health Solutions launches the brand CEREBIOME® (previously known as
  Probio'Stick®), a new name for an existing formula combining: Lactobacillus helveticus Rosell®-52
  and Bifidobacterium longum Rosell®-175" —
  https://www.lallemand.com/introducing-cerebiome-pioneering-psychobiotic-game-changing-science/
  Corroborated inside the catalogue: PMID 33658952 is recorded as "CEREBIOME (Lactobacillus
  helveticus R0052 and Bifidobacterium longum R0175)", and PMID 20974015 as "Probio'Stick
  (Lactobacillus helveticus R0052 and Bifidobacterium longum R0175)".
  The `cerebiome` record is PMID 42628338, written by the Rosell Institute (Lallemand) itself:
  "This study aimed to investigate the effects of the Cerebiome® probiotic supplement" — PMID 42628338.

- lgg  ->  gg   (the surviving key is gg; per-part alias. LGG is just the abbreviation of
  Lactobacillus rhamnosus GG. Today it appears only inside blends — `bb12+lgg+magnesiumchloride`
  and `bb12+lgg+palmitoylethanolamidepea` — so it merges no whole key, but it keeps one organism
  under one code.)
  Source: "Lactobacillus rhamnosus GG ATCC 53103 (LGG)" (title) —
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4747532/ (PMID 26861405)

- atcc53103  ->  gg   (the surviving key is gg; per-part alias. ATCC 53103 is the deposit number of
  strain GG. Only inside the blend `atcc53103+dsm32269+dsm32946+dsm34532+partiallyhydrolysedguargum`,
  so again no whole-key merge.)
  Source: "ATCC accessioned progeny of Lactobacillus rhamnosus strain GG cited in US Pat. No.
  4,839,281 as 53103"; "L. rhamnosus GG (ATCC 53103)" —
  https://microbewiki.kenyon.edu/index.php/Lactobacillus_rhamnosus_GG_(ATCC_53103)_and_its_Probiotic_Use
  and https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4249962/

- a1  ->  mcc1274   (the surviving key is mcc1274, because "a1" on its own is a dangerously generic
  token and MCC1274 is the maker's unique catalogue number. This merges `a1` (3 records: PMIDs
  30423465, 30569089, 31090457) with `mcc1274` (1 record: PMID 35570493) into one 4-record entity.
  See the record problem below for `a1+mcc1274`.)
  Source: FDA GRAS Notice 1002 lists the strain as "Bifidobacterium breve MCC1274; B. breve B-3;
  B. breve A-1; B. breve A1" — https://www.fda.gov/media/155711/download
  Corroborated inside the catalogue: PMID 32623402 is recorded as "Bifidobacterium breve A1 (MCC1274)".

- 431  ->  lcasei431   (surviving key `lcasei431`; per-part alias. Both records mean Chr. Hansen's
  single strain L. CASEI 431. I suggest `lcasei431` as the survivor because the bare token "431" is
  ambiguous, but either direction is mechanically fine — the main session should pick. This merges
  no two whole keys: `431` is PMID 41318456 alone, and `lcasei431` sits inside a vitamin blend.)
  Source: "L. casei 431 is produced by Chr. Hansen A/S ... The full scientific name is Lactobacillus
  paracasei subsp. paracasei, L. casei 431" —
  https://global.theprobioticsinstitute.com/en/chr-hansen-probiotics/l-casei-431
  The catalogue record reads "capsules containing Lactobacillus casei 431" — PMID 41318456.

## Joins I suspect but could not prove

- moodamin  ->  r0052+r0175   what is missing: the paper names no strain codes at all. Full text
  (PMC13097662) says only: "The probiotic supplement (Moodamin capsuls) provided from Amin
  pharmacytical company, Iran, was freeze-dried containing Lactobacillus helveticus and
  Bifidobacterium Longum bacteria ... at a dose of 2.682 × CFU and 0.318 × CFU each capsule,
  respectively" — PMID 41826906. The 2.682 : 0.318 ratio is 90 % : 10 %, which is the Cerebiome
  ratio, and L. helveticus + B. longum is an unusual pair, so R0052 + R0175 is likely. But I found
  no Amin Pharmaceutical page or any other document naming Moodamin's strains, and the brief's rule
  is that a guess is worse than nothing. **Do not join this without a manufacturer source.**

## Not the same entity, although they look alike

- r0052  vs  r0052+r0175   why: `r0052` is one strain on its own (PMID 25604727, a three-arm trial
  that also gives `r0033` and `r0071` separately). A single strain is never joined to a blend.
- r0033 / r0071 / rosell179  vs  anything   why: each is a different Lallemand/Rosell organism —
  B. longum ssp. infantis R0033, B. bifidum R0071, Bacillus subtilis Rosell-179. The shared "Rosell"
  prefix means one supplier, not one strain. All three are single-record, single-strain keys and
  stay as they are.
- r0052+r0175+r1012  vs  r0052+r0175   why: the three-strain blend (PMID 35405944, adds
  Lactiplantibacillus plantarum R1012) is a different entity from the two-strain pair. A blend is
  not its parts.
- rosell175+rosell52+sadenosylmethionine  vs  r0052+r0175   why: PMID 36411659 adds S-adenosyl
  methionine, which is an `other_actives` part of the key, so it stays a separate entity. The two
  Rosell aliases above will still rewrite it to `r0052+r0175+sadenosylmethionine`, which is correct.
- dn114001  vs  dn173010   why: two different Danone strains in two different products. DN-114 001
  is Lactobacillus casei (Actimel), deposited CNCM I-1518; DN-173 010 is Bifidobacterium animalis
  subsp. lactis (Activia), deposited CNCM I-2494. Different species.
  Source: "Compositions comprising lactobacillus casei cncm i-1518 (dn-114001)" (patent title) —
  https://patents.google.com/patent/EP2323675B1/en ; and PMID 38830472's own wording
  "Bifidobacterium animalis subsp. lactis DN-173 010/CNCM I-2494".
- cncmi1518  vs  anything   why: **there is no `cncmi1518` key in `entity-keys.txt`.** The brief
  lists it, but a grep of the file finds only `cncmi1079`, `cncmi1519+...`, `cncmi2494+dn173010+honey`,
  `cncmi3446`, `cncmi3690`, `cncmi4036`. Nothing to join.
- bl04  vs  bi04   why: **different species.** `bl04` is *Bifidobacterium longum* BL04, a Probiotical
  strain sold in the BIFIZEN blend — both catalogue records agree: "Bifidobacterium longum BL04"
  (PMID 40077722) and "Bifidobacterium longum 04" (PMID 37720373).
  Source: "Probiotic blend 04 + LF16 + LP01™ + LR06" —
  https://www.probiotical.com/en/products/probiotic-blend-04-lf16-lp01-lr06/
  `bi04` comes from PMID 35677549, which writes "*Bifidobacterium lactis* BI04" — a
  *B. animalis* subsp. *lactis*. Joining them would merge two different organisms. See the record
  problem below: `bi04` is itself very probably a capital-I misprint of Danisco's **Bl-04**, but the
  fix is in that record, not an alias.
- bi040+bl020+la120+lc130+lr110  vs  bl04 / bi04   why: PMID 38178223 spells its own strains
  "Bifidobacterium (B.) lactis BI040, B. longum BL020, Lactobacillus (L) rhamnosus LR110, L. casei
  LC130, L. acidophilus LA120" — a Ukrainian five-strain capsule with its own code series ending in
  a zero. These are not Bl-04, and it is a five-strain blend besides.
- bl999  vs  bl99   why: different species and different makers. BL999 is *Bifidobacterium longum*
  ATCC BAA-999 (Nestlé/Morinaga BB536 lineage), in PMID 21393113. BL-99 is *Bifidobacterium
  animalis* subsp. *lactis*, deposited CGMCC No. 15650 and owned by Inner Mongolia Yili, in
  PMID 41978217.
  Sources: "Bifidobacterium longum ATCC BAA-999 (BL999) and weight control" (patent title) —
  https://patents.google.com/patent/EP2308499A1/en ; "Bifidobacterium lactis BL-99 ... deposit
  number CGMCC No. 15650" — https://pmc.ncbi.nlm.nih.gov/articles/PMC8358461/
  Both are also parts of larger blends, so neither could merge with a single-strain key anyway.
- bl020  vs  bl04 / bl999 / bl99   why: BL020 belongs to the PMID 38178223 Ukrainian code series
  above. No evidence links it to any other key.
- shirota  vs  (nothing)   why: I searched `entity-keys.txt` for `yit`, `9029` and `yakult` and
  found **no** other key for this strain. All 12 `shirota` records already share one key; the
  species-name drift (Lactobacillus casei -> Lacticaseibacillus casei -> Lacticaseibacillus
  paracasei) does not change the key, because the key is built from the strain code "Shirota".
  Nothing to join.

## Record problems (not aliases)

- **PMID 30026567** — key `gg`, recorded as "Ergyphilus Plus (four strains)". The record keeps a
  four-strain product under a single-strain key, which silently pools it with eight true
  L. rhamnosus GG trials. Ergyphilus Plus (Nutergia) contains "Lactobacillus rhamnosus GG ATCC
  53103 ... Lactobacillus paracasei LMG P-21380 ... Lactobacillus acidophilus DSM 21717 ...
  Bifidobacterium bifidum DSM 22892", plus fructo-oligosaccharides, vitamin C and vitamin B3
  (https://www.nutergia.com/fr/fr/nos-complements-alimentaires/probiotiques/ergyphilus-plus).
  The right value is probably strain_codes = GG (or ATCC 53103), LMG P-21380, DSM 21717,
  DSM 22892 — giving a key like `dsm21717+dsm22892+gg+lmgp21380` — and the FOS / vitamin C /
  vitamin B3 question needs the same judgement the catalogue applies elsewhere to excipients.
  **This is the highest-value fix on my list: it is a wrong pooling that exists today.**

- **PMID 32623402** — key `a1+mcc1274`. One strain has been recorded twice, under both of its names
  ("Bifidobacterium breve A1 (MCC1274)"). The right value is a single strain code, MCC1274, giving
  key `mcc1274`. Note the alias `a1 -> mcc1274` does **not** fix this record — it would only turn
  the key into `mcc1274+mcc1274`. The record itself must lose the duplicate code.

- **PMID 38830472** — key `cncmi2494+dn173010+honey`. Same problem: "Bifidobacterium animalis
  subsp. lactis DN-173 010/CNCM I-2494" is one strain written with its trade code and its deposit
  number. The right value is one strain code, giving key `dn173010+honey`. Again an alias cannot
  fix it (it would give `dn173010+dn173010+honey`); the record must drop the duplicate.

- **PMID 38891799** — key `rosell17+rosell52`, recorded as "Sanprobi Stress (Lactobacillus
  helveticus Rosell-52 and Bifidobacterium longum Rosell-17)". The record copies the paper
  faithfully, but **the paper itself has a typo**: Sanprobi Stress is Rosell-52 + Rosell-**175**.
  Source: the manufacturer's own product page lists "Lactobacillus helveticus Rosell-52,
  Bifidobacterium longum Rosell-175" — https://sanprobi.pl/en/produkty-sanprobi/sanprobi-stress/
  The right value is Rosell-175, giving key `rosell175+rosell52` and, after the aliases above,
  `r0052+r0175`. That makes this a **thirteenth** record for the Lallemand pair. I did not propose
  `rosell17 -> rosell175` as an alias, because "Rosell-17" is not a real second name for the
  strain — it is a missing digit, and aliasing it would hide a mistake that should be corrected.

- **PMID 35677549** — key `bi04+fructooligosaccharide+gl104+lpl28+mp108`, from "*Bifidobacterium
  lactis* BI04" in the paper. The species is right for Danisco's **Bl-04** (*B. animalis* subsp.
  *lactis*, ATCC SD5219, DGCC2908), and "BI04" is the classic capital-I-for-lower-case-L misreading.
  Source: "Bl-04 (also known as DGCC2908 and RB 4825) ... deposited at the American Type Culture
  Collection safe deposit as strain SD5219" — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2698493/
  I am **not** proposing an alias, for two reasons: the paper may genuinely be using a different
  Taiwanese strain alongside GL104 / LPL28 / MP108, and — more important — `bl04` is already taken
  in this catalogue by *Bifidobacterium longum* BL04, so an alias `bi04 -> bl04` would merge two
  different species. If the record is corrected to "Bl-04", the correction must use a code that
  does not collide with B. longum BL04 (ATCC SD5219 would be unambiguous).

- Minor, no action needed: PMID 40722352 is keyed `gg` but described as "Lacticaseibacillus
  rhamnosus GG with Bifidobacterium longum". If the B. longum was in the product and not in the
  comparator, this is a two-strain entity wrongly keyed as one strain. I did not have the paper's
  arm structure in front of me, so I flag it rather than assert it. Worth one look.

## Could not find out

- **Moodamin's strain codes.** I read the full text (PMC13097662) and it names none. I searched for
  "Moodamin" on the web, for Amin Pharmaceutical Iran, and for Iranian L. helveticus + B. longum
  mood products; nothing returned a composition sheet for this product. Left unjoined on purpose.
