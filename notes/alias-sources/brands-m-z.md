# Brand-named entity keys, M–Z (excluding the De Simone family and OMNi-BiOTiC)

Every key on my list was looked up, its composition sourced where a source exists, and then
checked against every other key in `entity-keys.txt`. The short version: **no alias join is
confident enough to apply.** The three specific questions are answered below, two of them as
record problems and one as "both keys are correct".

## Joins I am confident about

- (none)

## Joins I suspect but could not prove

- `erythromycin+pro450dlactatefreemultistrain`  ->  `bl04+br03+bs01+gg`
  what is missing: agreement between sources on the strain codes, **and** the erythromycin.
  Pro4-50 (SpectrumCeuticals, Australia) is a four-strain product whose largest component is
  *Lacticaseibacillus rhamnosus* GG plus three bifidobacteria, which is the same shape as
  PMID 40077722's blend (`bl04+br03+bs01+gg` = BS01, BR03, BL04, GG). But the two retail
  sources give **different codes for the three bifidobacteria**:
  - "Lactobacillus rhamnosus GG: 25 billion CFUs; Bifidobacterium lactis BS01: 15 billion;
    Bifidobacterium breve BR03: 5 billion; Bifidobacterium longum BL03: 5 billion" —
    https://www.mrvitamins.com.au/products/spectrumceuticals-pro4-50-d-lactate-free
  - "Lactobacillus rhamnosus GG 25 billion CFU; Bifidobacterium lactis BL21 15 billion CFU;
    Bifidobacterium breve BB23 5 billion CFU; Bifidobacterium longum BL05 5 billion CFU" —
    https://www.naturalchemist.com.au/spectrumceuticals-pro4-50-multistrain-probiotic-60-capsules/
  Only GG is consistent. I will not guess between BS01/BR03/BL03 and BL21/BB23/BL05.
  **Even if the codes matched, this join must not be made**, because the catalogue key for
  PMID 29409505 includes `erythromycin` (a co-administered drug) and the other key does not.
  Those are different entities under rule 4. I record it only so nobody re-opens it.

## Not the same entity, although they look alike

- `ultrabiotic60`  vs  `lab4`   why: UltraBiotic 60 (BioCeuticals, Australia) **contains** the
  Lab4 strains but is much more than Lab4. Its label reads: "Lactobacillus acidophilus (CUL21
  + CUL60) 20 billion CFU, Lactobacillus rhamnosus (CUL63) 15.55 billion, Lactobacillus casei
  (CUL06) 9.45 billion, Bifidobacterium animalis ssp. lactis (CUL34) 6.55 billion,
  Lactobacillus plantarum (CUL66) 3.15 billion, Streptococcus thermophilus (CUL68) 2.25
  billion, Lactobacillus fermentum (CUL67) 1.35 billion, Bifidobacterium breve (Bb-18) 1.35
  billion, Bifidobacterium bifidum (CUL20) 345 million" —
  https://www.chemistwarehouse.com.au/buy/114005/bioceuticals-ultrabiotic-60-60-capsules
  Lab4 is only CUL60 + CUL21 + CUL34 + CUL20. Nine strains is not four strains, so this is the
  "a blend is not its parts" trap. Do not join. Also do not join `ultrabiotic60` to
  `cul20+cul21+cul34+cul60+cul66+vitaminc+vitamind+zinc` (Lab4P), for the same reason.

- `sim01` / `prebiotics+sim01`  vs  `sim03`   why: both come from the same Hong Kong group
  (CUHK / Microbiota I-Center), but they are different formulas. SIM01 is three adult strains
  (*B. adolescentis*, *B. bifidum*, *B. longum*) with three prebiotics; SIM03 is an infant
  formula built on "unique Bifidobacterium bifidum and Bifidobacterium breve strains"
  (PMID 38326388). Different strain sets, different entities.

- `providac`  vs  `bb12+inulin23g+la5`, `bb12+la5+vitamind+vitamine`   why: Providac is
  exactly LA-5 + BB-12 ("Lactobacillus Acidophilus LA-5 and Bifidobacterium BB-12",
  https://www.onlinegenericmedicine.com/providac-capsule-lactobacillus-acidophilus-and-bifidobacterium).
  That is the same **bacteria** as those two keys, but each of those keys also carries a
  non-bacterial active (inulin 2.3 g; vitamin D and vitamin E) that is part of the key under
  rule 4. There is no plain `bb12+la5` key in the inventory, so there is nothing to join to.

## Record problems (not aliases)

- **PMID 37111201 (`sim01`) — the prebiotics are missing from the key.** SIM01 is itself a
  synbiotic and always contains its three prebiotics. Source: "SIM01 is a micro-encapsulated
  lyophilised powder containing 20 billion colony-forming units of three bacterial strains,
  B adolescentis, Bifidobacterium bifidum, and Bifidobacterium longum with three prebiotic
  compounds including galacto-oligosaccharides, xylo-oligosaccharides, and resistant dextrin"
  — https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(23)00685-0/fulltext
  (PMID 38071990), and the product page https://www.g-niib.com/en/products/g-niib-immunity-plus-sim01.
  So `sim01` (PMID 37111201) and `prebiotics+sim01` (PMID 38071990) describe **one product**.
  The difference is a recording difference, not a real one. Fix by recording both the same way
  — I suggest dropping the separate `prebiotics` other-active from PMID 38071990, because the
  prebiotics are inside the branded product, exactly as `vivomixx` or `vsl3` would be. Once
  both records read `sim01`, they pool into one key with 2 records without any alias entry.
  (Note that this is also the **correct** answer to "is this an alias?" — it is not.)

- **PMID 42414927 (`pedilact`) — the fructo-oligosaccharide is missing from the key.** Pedilact
  (Zist Takhmir, Iran) is a synbiotic; the FOS is always in it. Source: the manufacturer's
  composition as quoted in the trial literature — "L. rhamnosus ATCC 15820 (1 × 10^10 CFU/mL),
  L. reuteri ATCC 55730 (2 × 10^9 CFU/mL), and Bifidobacterium longum subsp. infantis ATCC
  15697 (1.5 × 10^9 CFU/mL) ... contains the prebiotic fructo-oligosaccharide", Zist Takhmir
  PediLact product page (https://zisttakhmir.com/en/product/pedilact — the /en/ page 404s for
  automated fetch; the same list is reproduced in
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5141660/ and in the colic trial PMC9374146).
  So `pedilact` and `fructooligosaccharide+pedilact` are **one product**, recorded two ways.
  Same fix as SIM01: make the two records agree, and they pool with no alias entry.
  Caution: PMID 35968208's abstract names only "Lactobacillus reuteri", which understates the
  product; the three strains above are what Pedilact drops actually contain.

- **PMID 16957676 (`estromineralserena+magnesium+magnoliabarkextract+soyisoflavones`) — calcium
  and vitamin D3 look dropped.** The paper's own title is "Soy isoflavones, lactobacilli,
  Magnolia bark extract, vitamin D3 and calcium" and its methods say "soy isoflavones (60 mg),
  lactobacilli (500 millions spores), calcium (141 mg) ... magnesium (50 mg)". If the rule is
  that every other-active goes in the key, `calcium` and `vitamind3` belong there too. No
  other key is affected either way.

- **PMID 34211197 (`providac`) — the key could name the strains.** Providac is LA-5 + BB-12
  (source above), so the key could be recorded as `bb12+la5`. That still matches no other key
  today, so this is a clarity improvement, not a pooling gain.

- **PMID 25038208 (`velgut`) — Velgut contains fructo-oligosaccharide.** "Velgut contains
  Bifidobacterium Breve, B. Longum, B. Infantis, Lactobacillus Acidophilus, L. Plantarum,
  L. Rhamnosus, L. Casei, Streptococcus Thermophilus, and Saccharomyces boulardii ... include
  fructooligosaccharides" — https://www.truemeds.in/medicine/velgut-100-mg-capsule-15-TM-CACR1-009701.
  Whether that is worth adding depends on whether the FOS is treated as inside the brand (as I
  recommend for SIM01 and Pedilact). Flagging it so the treatment is consistent across the
  three.

- **PMIDs 31390762 (`inulin+oatbran+pectin+resistantstarch+synbiotic2000forte`) — "oat bran"
  is probably "beta-glucan".** The manufacturer's four fibres are "betaglucan, inulin, pectin
  and resistant starch" (https://synbiotic2000.com/ ; also Bengmark 2012,
  https://onlinelibrary.wiley.com/doi/full/10.1186/2001-1326-1-6). Oat bran is the usual source
  of that beta-glucan, so this is likely a paraphrase rather than an error, but both
  Synbiotic 2000 Forte keys should use the same word (they do today, so nothing breaks).

## Answers to the three specific questions

1. **SIM01 — one product, not two.** SIM01 is itself a synbiotic and always contains its three
   prebiotics. This is a **record problem**, not an alias. Details above.
2. **Pedilact — one product, not two.** Pedilact drops always contain fructo-oligosaccharide.
   This is a **record problem**, not an alias. Details above.
3. **Synbiotic 2000 Forte — two genuinely different arms; both keys are correct.** PMID
   31390762 is a three-arm trial: "Participants with overt HE were randomised in a blinded
   placebo-controlled study to receive synbiotics, BCAAs, or a combination of BCAAs and
   Synbiotics" (abstract, PMID 31390762). The synbiotic-alone arm and the synbiotic+BCAA arm
   are separate randomised groups, so `inulin+oatbran+pectin+resistantstarch+synbiotic2000forte`
   and `branchedchainaminoacids+inulin+oatbran+pectin+resistantstarch+synbiotic2000forte` are
   two real entities. **No alias.** (Composition of the product itself, for the record: "10^11
   of each of four lactic acid bacteria: Pediococcus pentosaceus 5-33:3, Leuconostoc
   mesenteroides 32-77:1, Lactobacillus paracasei subsp paracasei 19, and Lactobacillus
   plantarum 2362, along with 2.5 g of each of four fermentable fibres" — https://synbiotic2000.com/)

## Checked, composition found, no match anywhere in the inventory

Each of these is a real product whose composition I could source, and each is the only key in
`entity-keys.txt` for that product. Nobody needs to look again.

- `met2` (PMID 35060914) — MET-2, NuBiyota: "40 strains of bacteria that were purified and
  lab-grown from the stool of a single healthy donor" (abstract, PMID 35060914; see also
  https://ncbi.nlm.nih.gov/pmc/articles/PMC8817211). A defined 40-strain donor-derived
  consortium; nothing else in the inventory resembles it. **No match.**
- `nourishkefir` (PMID 41286799) — plain organic cow's-milk kefir; "Nourish Kefir supplied
  organic cow's milk kefir" (competing-interests statement, PMID 41286799). Undefined mixed
  culture, so it can never be proved equal to another key. The only other kefir key,
  `39920878 Kefir fortified with Lactobacillus helveticus R0052 and Bifidobacterium longum
  R0175`, is a *fortified* kefir and is a different entity. **No match.**
- `sb121` (PMID 36997569) — SB-121, Scioto Biosciences: "a combination of L. reuteri,
  Sephadex (dextran microparticles), and maltose" (abstract, PMID 36997569). The dextran
  carrier is part of the product. No other key pairs *L. reuteri* with dextran. **No match.**
- `sim03` (PMID 38326388) — "microencapsulation technology to protect the viability of unique
  Bifidobacterium bifidum and Bifidobacterium breve strains identified through big data
  analysis" (abstract, PMID 38326388). Strain codes are not published. **No match.**
- `ultrabiotic60` (PMIDs 31006545, 32847731) — nine strains, quoted above. Both records already
  sit on one key, which is right: both trials gave UltraBiotic 60 plus SB Floractiv
  (*S. boulardii*) during the international-competition stage, so they are the same regimen.
  **No match elsewhere**, and see the Lab4 warning above.
- `velgut` (PMID 25038208) — nine strains plus FOS, quoted above. Species-level only, no strain
  codes, so no join is provable. It is **not** VSL#3-like: it adds *L. rhamnosus* and
  *S. boulardii* and lacks *L. delbrueckii* subsp. *bulgaricus*. **No match.**
- `providac` (PMID 34211197) — LA-5 + BB-12, quoted above. **No match** (see the "look alike"
  section for why the two `bb12+la5+...` keys are not it).
- `coenzymeq10+magnesiumorotate+nrgbiotic` (PMID 39242786) — NRGBiotic, Medlab: "a combination
  of lyophilized probiotics (Lactobacillus acidophilus, Bifidobacterium bifidum, Streptococcus
  thermophilus) with a total CFU of 2 × 10^10, Mg Orotate 1600 mg and CoQ10 150 mg"
  (https://www.nature.com/articles/s41598-024-71093-z, PMID 39242786). Species-level only, and
  the two non-bacterial actives are part of the key. **No match.**
- `galactooligosaccharide+maltodextrin+scm06` (PMID 41535300) — "SCM06 combines two prebiotics
  (maltodextrin and galactooligosaccharide) and 5 billion CFU of four probiotic species,
  including Bifidobacterium bifidum, Bifidobacterium longum, Lactobacillus plantarum, and
  Streptococcus thermophilus" (https://www.nature.com/articles/s41522-025-00902-8, PMID
  41535300). Species-level only. **No match.**
- `heatkilled+jk5g` (PMIDs 37601658, 41859075) — "a formulation of inactivated Lactobacillus
  strains and metabolites" (abstract, PMID 41859075). The two records are already on one key,
  which is correct — both are JK5G postbiotics. Strain codes are not published, so no further
  join is possible. **No match.**
- `heatkilled+keystone` (PMID 42486470) — a fermented, pasteurised oat preparation, so a
  postbiotic food rather than a named strain set. The only other oat key,
  `40572644 Lactococcus cremoris FBMS_5810 on oat flakes`, is a live single strain on oats and
  is a different entity. **No match.**
- `cuscutaseedextract+heatkilled+mt104` (PMID 40583505) — "MT104, A Dietary Supplement Based on
  Cuscuta Seeds and [heat-killed probiotics]" (title/abstract, PMID 40583505). The botanical is
  part of the key and nothing else in the inventory contains Cuscuta. **No match.**
- `estromineralserena+magnesium+magnoliabarkextract+soyisoflavones` (PMID 16957676) — "soy
  isoflavones (60 mg), lactobacilli (500 millions spores), calcium (141 mg) ... magnesium
  (50 mg) (Estromineral serena, ES)" (abstract, PMID 16957676). The lactobacilli are never
  named to species, let alone strain. **No match** (see record problem above).

## Could not find out

- **Strain codes for `velgut`, `providac` beyond LA-5/BB-12, `scm06`, `nrgbiotic`, `sim03`,
  `jk5g` and `keystone`.** I searched the manufacturers' pages, retail listings and the trial
  papers. These products publish species names only, or nothing at all. That is a real
  property of the products, not a gap in my searching, and it means these keys can never be
  safely joined to a strain-coded key. Leaving them separate is the correct outcome.
- **Which strain codes Pro4-50 really uses.** Two Australian retailers of the same product give
  two different sets of codes (above). I did not find a manufacturer datasheet. Moot for the
  alias question, because of the erythromycin in the key.
