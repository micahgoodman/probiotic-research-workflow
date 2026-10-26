# Brand-named entity keys, A to L

Scope: the 33 brand keys assigned to me (cerebiome skipped, another agent holds it).
Every claim below has a source. Where I could not find a source, I say so.

## Joins I am confident about

- `biokultadvanced`  ->  `pxn21+pxn23+pxn25+pxn27+pxn30+pxn35+pxn37+pxn39+pxn45+pxn47+pxn54+pxn57+pxn63+pxn66`
  (the surviving key is the PXN one, because it names the strains instead of the brand)
  Both records name the same branded product, Bio-Kult Advanced, and both say fourteen
  strains: PMID 37314797 "Bio-Kult Advanced (fourteen strains)" and PMID 35129111
  "Bio-Kult Advanced (14 strains)" with the fourteen PXN codes written out.
  Source: the maker's own strain list for Bio-Kult Advanced — "Bacillus subtilis PXN 21,
  Bifidobacterium bifidum PXN 23, Bifidobacterium breve PXN 25, Bifidobacterium infantis
  PXN 27, Bifidobacterium longum PXN 30, Lactobacillus helveticus PXN 35, Lactobacillus
  paracasei PXN 37, Lactobacillus delbrueckii ssp. bulgaricus PXN 39, Lactobacillus
  helveticus PXN 45, Lactobacillus plantarum PXN 47, Lactobacillus rhamnosus PXN 54,
  Lactobacillus salivarius PXN 57, Lactococcus lactis ssp. lactis PXN 63, Streptococcus
  thermophilus PXN 66" — https://www.bio-kult.com/p/everyday-gut/13412724/ (14 strains,
  2 x 10^9 CFU per capsule). No reformulation of the fourteen-strain Advanced formula is
  recorded between the two trials (35129111, 2022; 37314797, 2023).

- `familact+fructooligosaccharides`  ->  `familact+fructooligosaccharide`
  (either direction is fine; this is a spelling variant, not a different ingredient)
  PMID 34466612 records "fructooligosaccharides" and PMID 36745650 records
  "fructo-oligosaccharide" for the same branded synbiotic, Familact. One product, one
  prebiotic, two spellings.
  Source: the maker's product page — "FamiLact ... contains high amounts of 9 safe and
  beneficial bacterial strains plus fructooligosaccharides as prebiotic" (Zist Takhmir,
  via https://www.irex2world.com/en/iran-exports-product/3451/zist-takhmir/familact).

## Joins I suspect but could not prove

- `ab001+fermentedricebran+lcysteine`  ->  `ab001`
  What is missing: nothing about the product — the two trials used the same supplement from
  the same maker (de Faire Medical AB, same research group). The block is a recording
  difference, not a product difference: AB001 *is* fermented rice bran plus L-cysteine, so
  PMID 35769391 listed the brand's own ingredients in `other_actives` while PMID 36686368
  left the field empty. Fix the record (see "Record problems") and the keys become equal
  without any alias at all.
  Source: "AB001 consists of naturally fermented rice bran containing Bacillus subtilis,
  B. coagulans, L-Cysteine and Dextrin" ... "Contents/dose (800 mg): fermented rice bran
  560 mg, L-Cysteine 200 mg, dextrin 4 mg and excipients 36 mg" — PMID 35769391
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC9234833/).

- `familact` (PMID 42162021)  ->  `familact+fructooligosaccharide`
  What is missing: confirmation of which Familact SKU the 2026 zinc trial used. Familact as
  sold always contains FOS (source above), so the FOS-free key is probably an omission. But
  I cannot read the trial's Methods from the abstract, and Zist Takhmir also sells
  "Familact 2plus", so I will not assert it. Same fix-the-record route as AB001.

- `duolaccarenoncoated`  ->  `duolaccaredualcoated` (one decision for the main session)
  Both arms are the same trial (PMID 27178566) and the same six CBT strains; the only
  difference is Cell Biotech's dual coating, which is a delivery shell, not a strain.
  RULES.md rule 4 says the vehicle does not change the entity, which argues for one key.
  Against it: joining them merges two arms of a single trial, and the trial exists to test
  the coating. I am flagging it rather than proposing it, because the choice is about how
  the catalogue counts arms, not about what the product is.
  Source: "DUOLAC Care ... 100% Korean CBT strain formulation with 6 probiotic strains
  (CBT-LA1 L. acidophilus, CBT-LR5 L. rhamnosus, CBT-ST3 S. thermophilus, CBT-BF3
  B. bifidum, CBT-BL3 B. lactis, CBT-BG7 B. longum)" — https://duolac.sg/product/duolac-care/
  and the dual-coating description at
  https://www.duolac.com/worldwide-patented-dual-coating-technology/

## Not the same entity, although they look alike

- `lab4`  vs  `cul20+cul21+cul34+cul60+cul66+vitaminc+vitamind+zinc`   why: Lab4 is four
  strains; the inventory key is Lab4**P**, which is Lab4 plus a fifth strain (CUL66) and
  also carries vitamin C, vitamin D and zinc. A blend is not the same as a bigger blend.
  Source: "The Lab4 probiotic consortium comprises Lactobacillus acidophilus CUL21 (NCIMB
  30156), L. acidophilus CUL60 (NCIMB 30157), Bifidobacterium bifidum CUL20 (NCIMB 30153)
  and B. animalis subsp. lactis CUL34 (NCIMB 30172)" —
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12993548/ ; the Lab4 trial itself (PMID 38287443)
  was run by Cultech Limited, the owner of Lab4. The inventory record 41909887 already
  writes "Lab4P (CUL21, CUL60, CUL66, CUL20, CUL34)". There is no plain four-CUL key in the
  inventory, so `lab4` has no partner.

- `i31`  vs  `cect7483+cect7484+cect7485+vitamind`   why: same three strains, but the other
  record's product was given with vitamin D, and rule 4 makes a co-ingredient part of the
  key. Strain-wise they are the same blend; entity-wise they are not. If the main session
  ever decides the vitamin D there is inherent to the brand rather than added, this becomes
  a join — worth a second look at PMID 38445822.
  Source: "i3.1 is a probiotic blend of 3 patented strains (P. acidilactici KABP 021/CECT
  7483, L. plantarum KABP 022/CECT 7484, L. plantarum KABP 023/CECT 7485)" —
  https://www.ingredientsnetwork.com/i3-1-prod1281073.html ; the I.31 trial is PMID 25024629.
  Also not the same as `cect7480+cect7485+kabp023+kabp052+vitamind` (different strain set).

- `bifico`  vs  `livecombinedbifidobacteriumandlactobacillustablets`   why: two different
  Chinese registered products. Bifico (培菲康, Shanghai Sine) is the triple-viable
  *capsule* of Bifidobacterium longum, Lactobacillus acidophilus and Enterococcus faecalis —
  its English label name always names Enterococcus: "live combined Bifidobacterium,
  Lactobacillus, and Enterococcus powder/capsule" (PMID 37119032, title of the Chinese
  expert consensus). "Live Combined Bifidobacterium and Lactobacillus Tablets" is the
  Golden Bifid tablet from Inner Mongolia Shuangqi Pharmaceutical, which is
  Bifidobacterium (longum), Lactobacillus bulgaricus and Streptococcus thermophilus —
  "Golden Bifido is a probiotic mixture containing live Lactobacillus bulgaricus,
  Bifidobacterium and Streptococcus thermophilus", and the tablet drug entry names Inner
  Mongolia Shuangqi as its developer
  (https://synapse.patsnap.com/drug/9ca47c9f17e64d989c39720be12a71ed). Different species,
  different maker, different dosage form. Do not join.
  The trial record agrees it is a tablet given as "2 g three times daily" (PMID 40793826),
  which is the Golden Bifid tablet dose, not the Bifico capsule dose.

- `bifidobacteriumquadrupleviabletablet`  vs  `bifico`   why: the quadruple (tetragenous)
  tablet has four organisms including an aerobe that Bifico does not contain.
  Source: "Bifidobacterium Tetragenous viable Bacteria Tablets is comprised of four strains,
  including Bifidobacterium infantis CGMCC0460.1, Lactobacillus acidophilus CGMCC0460.2,
  Enterococcus faecalis CGMCC0460.3, and Bacillus cereus CGMCC0460.4" —
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7329396/ (the protocol for the same kind of
  D-IBS trial as PMID 36717369).

- `comflor`  vs  `comflor+zinc`   why: these are the two arms of one trial (PMID 39803228);
  one arm really did get zinc as well. A real difference, not a recording slip.

- `k11`  vs  `k11tmax+magnesium+selenium+vitamina+zinc`   why: two arms of one trial
  (PMID 41547752). K11-TMAX is the same kefir-derived mixture with minerals and vitamin A
  added — "182 children with ASD were randomly assigned (1:1:1) to the placebo, K11, or
  K11-TMAX groups" (PMID 41547752). Different entity by rule 4.

- `lactocare`  vs  `lactocare+vitamind`   why: PMID 29432877 gave vitamin D as well. Real
  difference. (See the record problem below about what Lactocare contains.)

- `colicron`  vs  `bb12+lgg+palmitoylethanolamidepea`   why: both carry PEA, so they look
  alike, but the bacteria are not the same. Colicron is nine strains —
  "Lactobacillus acidophilus NCFM, Bifidobacterium longum BB536, Bifidobacterium lactis
  DSM 15954, Bifidobacterium breve M-16V, Lactobacillus casei LC-G11, Lactobacillus
  paracasei Lpc-37, Lactobacillus plantarum GMNL-14, Lactobacillus rhamnosus HN001,
  Streptococcus thermophilus Th-4" plus PEA 70 mg, Hericium erinaceus and Undaria
  pinnatifida — https://aliveda.com/en/products/colicron/ . The other key is Metagenics
  Ultra Flora Intensive Care (BB-12, LGG, S. boulardii) plus PEA (PMID 41709243).
  Caution: the Aliveda page is today's formula; the trial is PMID 38240683 (2024). I found
  no reformulation notice, but I could not prove the 2024 formula was identical.

- `acidolac+vitamind3`  vs  `gg` / `gg+inulin15g`   why: Acidolac is LGG **with FOS**, so it
  is not plain LGG, and the trial added vitamin D3 on top. Source: "Acidolac ... lyophilized
  cultures of Lactobacillus rhamnosus GG ATCC 53103 and fructooligosaccharides" (Polpharma,
  https://www.mp.pl/pacjent/leki/lek/85554,Acidolac-LGG-liofilizat). Caution: Polpharma sells
  several Acidolac variants (Acidolac Baby has different organisms); PMID 35912804 does not
  say which one, so even a `gg+fructooligosaccharide` key would not be safe to join.

- `lactibiane`  vs  any single-strain key (for example `r0052`)   why: it is a four-organism
  blend, and a blend is never one of its parts. PMID 36606510 states the composition:
  "one tablet containing Bifidobacterium longum, Lactobacillus helveticus, Lactococcus
  lactis, Streptococcus thermophilus/day" — that is PiLeJe's Lactibiane Référence
  (LA101/LA102/LA103/LA104). No code key for it exists in the inventory.

- `dailyeast`  vs  `ultrabiotic60`   why: DAILYEAST is Saccharomyces boulardii on its own
  (PMID 35255819); Ultrabiotic 60 is a bacterial blend that also contains S. boulardii.
  Blend is not its part.

## Record problems (not aliases)

- **PMID 35769391 (AB001).** `other_actives` lists "fermented rice bran" and "L-cysteine",
  but those are the branded product itself, not extras given on top: "AB001 consists of
  naturally fermented rice bran containing Bacillus subtilis, B. coagulans, L-Cysteine and
  Dextrin" (PMC9234833). The right value is almost certainly `other_actives: []`, which
  makes this key equal to `ab001` (PMID 36686368) with no alias needed. Two trials, one
  product, one maker.

- **The Familact group, four keys for one branded synbiotic.** Familact has a fixed sold
  composition: nine strains plus FOS (maker's page, quoted above). The strain counts in the
  records — nine (42162021), seven (36745650), eight (34466612), four (30217229) — are the
  papers' own loose descriptions, not four different products. Recommended clean-up:
  - 34466612 and 36745650: one spelling of FOS (alias above, or normalise the text).
  - 42162021: FOS missing although the product contains it.
  - 30217229: keep the selenium. Selenium was genuinely co-supplemented, not part of
    Familact — "8 x 10^9 CFU/day probiotic plus 200 μg/day selenium supplements" (abstract).
  If the catalogue's convention is that an ingredient inside the branded product does not go
  into `other_actives` (which is what the AB001, BioZenD, DS-01 and Colicron records already
  assume), then the cleanest end state is a single `familact` key for 42162021, 36745650 and
  34466612, and `familact+selenium200microgramperday` kept separate for 30217229. **This is
  a convention question, so I am reporting it, not applying it.** The two conventions are
  in conflict in the data today, and that conflict is what produced four keys here.

- **PMID 41599868 (DS-01).** `other_actives: ["pomegranate extract"]`. The pomegranate
  polyphenol is the product's own prebiotic: "DS-01 combines 24 select bacterial strains and
  a non-fiber polyphenol prebiotic compound: punicalagins, sourced from Indian Pomegranate"
  (https://help.seed.com/en-US/articles/ds-01-daily-synbiotic-295557). Same convention
  question as Familact. No join either way — DS-01 appears once.

- **PMID 38598329 (BioZenD).** Same pattern: the "D" in BioZenD is the vitamin D3 in the
  capsule, not an extra. "BioZenD contains Bacillus coagulans, Lactobacillus acidophilus,
  Lactobacillus paracasei, Lactobacillus reuteri, Lactobacillus rhamnosus and
  Bifidobacterium longum, with Vitamin D3 (400 IU)" —
  https://takgene.com/takgene-pharma/biozen-d/?lang=en . Six strains, which matches the
  record. No join available either way.

- **The three `lactocare` records may not be one product.** 35685534 and 41457283 both say
  four strains, but the maker describes LactoCare as a twelve-strain synbiotic with FOS
  (https://www.irex2world.com/en/iran-exports-product/3449/zist-takhmir/lactocare), and
  41951219 says only "Lactocare". Zist Takhmir sells several LactoCare forms (capsule,
  sachet, drops). I could not prove the three trials used the same form. They are **already**
  pooled under one key, so this is a possible over-pooling that someone should check against
  the three full texts. I am not proposing to split anything; I am flagging it.

## Could not find out

- `comflor`, `comflor+zinc` — what Comflor's strains are. I searched the web for the brand
  and for the trial (PMID 39803228, decompensated cirrhosis); the product returns no
  manufacturer page I could reach. No inventory key could be matched to it either way.
- `bioflora` (PMID 41450035) — the record already gives the species (L. acidophilus,
  B. lactis, B. longum) but no strain codes, and I found no manufacturer page for a
  probiotic named Bioflora matching an ADHD trial. Several unrelated products share the
  name. No inventory key has that species trio without codes, so no join is possible.
- `abiprolandbrexibiol+heatkilled` (PMID 39106427) — no source found for either Abiprol or
  Brexibiol. Web search returns nothing for these names. Note the key joins two products
  into one entity, which is right if both were given together, but nobody can check the
  strains without the full text.
- `flore+prebiotics` (PMID 38661344) — Flore is a personalised ("precision") synbiotic, so
  there may be no single fixed composition. I found no published composition for the
  research edition. A personalised product arguably cannot be an entity at all; worth a
  ruling.
- `alflorexbabydrops+pseudoceramidecream+topicalcalcineurininhibitor` (PMID 41686508) — I did
  not find a strain list for Alflorex Baby Drops (the adult Alflorex is B. longum 35624, but
  I will not carry that across to the baby drops without a source). No join is possible
  anyway, because the key carries two topical co-treatments.
- `lactofem` (PMID 38216917) — the maker's listing says seven strains (L. acidophilus,
  L. casei, L. bulgaricus, L. rhamnosus, B. longum, B. breve, S. thermophilus;
  https://irex2world.com/en/iran-exports-product/73mYOb3O), while the record says four. I
  could not settle which the trial used, and it does not matter for aliases: no other
  inventory key could be Lactofem.
- `exobdnf` (PMID 41597376) — I did find the strain: ExoBDNF is Pediococcus acidilactici
  SWP-CGPA01 (NCIMB 44102), 1.0 x 10^10 CFU
  (https://clinicaltrials.gov/study/NCT06968299). There is no matching strain key in the
  inventory, so: no match found.
- `dailyeast` (PMID 35255819) — record already names Saccharomyces boulardii; no strain code
  found for DAILYEAST, and no plain S. boulardii key exists in the inventory. No match.
- `duolaccaredualcoated` / `duolaccarenoncoated` — the six CBT strain codes are known (above),
  but the inventory holds no CBT-coded key other than `cbtlr5` (a single strain), which a
  blend must never be joined to. No match outside the trial itself.
- Everything else on my list — `acidolac+vitamind3`, `biozend+vitamind`, `colicron`, `ds01+
  pomegranateextract`, `i31`, `k11`, `k11tmax+...`, `lab4`, `lactibiane`, `lactocare`,
  `lactocare+vitamind`, `livecombinedbifidobacteriumandlactobacillustablets`,
  `bifidobacteriumquadrupleviabletablet`, `bifico` — **no match found** in
  `entity-keys.txt`. Nobody needs to look again.
