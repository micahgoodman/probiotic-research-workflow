# De Simone Formulation cluster — alias findings (21 September 2026)

The surviving key I propose for the real eight-strain De Simone Formulation is
`dsm24730+dsm24731+dsm24732+dsm24733+dsm24734+dsm24735+dsm24736+dsm24737`, because it is the
key with the most records (4) and it names the strains that every source uses.

The eight strains, as the maker lists them:
Streptococcus thermophilus DSM 24731 / NCIMB 30438; Bifidobacterium breve DSM 24732 / NCIMB 30441;
B. longum DSM 24736 / NCIMB 30435; B. infantis DSM 24737 / NCIMB 30436;
Lactobacillus acidophilus DSM 24735 / NCIMB 30442; L. plantarum DSM 24730 / NCIMB 30437;
L. paracasei DSM 24733 / NCIMB 30439; L. delbrueckii subsp. bulgaricus DSM 24734 / NCIMB 30440.

## Joins I am confident about

- ncimb30435+ncimb30436+ncimb30437+ncimb30438+ncimb30439+ncimb30440+ncimb30441+ncimb30442  ->  dsm24730+dsm24731+dsm24732+dsm24733+dsm24734+dsm24735+dsm24736+dsm24737
  (the surviving key is the DSM one, because it holds 4 records and the NCIMB one holds 1)
  Why: the Vivomixx label prints the two collection numbers side by side for every one of the
  eight strains, so this is one strain set under two deposit numbers, not two products.
  Source: "Streptococcus thermophilus DSM 24731® / NCIMB 30438 … Bifidobacterium breve DSM 24732® / NCIMB 30441 … Bifidobacterium longum DSM 24736® / NCIMB 30435 … Bifidobacterium infantis DSM 24737® / NCIMB 30436 … Lactobacillus acidophilus DSM 24735® / NCIMB 30442 … Lactobacillus plantarum DSM 24730® / NCIMB 30437 … Lactobacillus paracasei DSM 24733® / NCIMB 30439 … Lactobacillus delbrueckii subsp. bulgaricus DSM 24734® / NCIMB 30440" — https://ayp.healthcare/vivomixx-probiotic-450-billion-30-sachets
  Second source (NCIMB-only list, same eight organisms, official Vivomixx site): "Streptococcus thermophilus NCIMB 30438 / Bifidobacterium breve NCIMB 30441 / Bifidobacterium longum NCIMB 30435 / Bifidobacterium infantis NCIMB 30436 / Lactobacillus acidophilus NCIMB 30442 / Lactobacillus plantarum NCIMB 30437 / Lactobacillus paracasei NCIMB 30439 / Lactobacillus delbrueckii subsp. bulgaricus NCIMB 30440" — https://dsf.vivomixx.eu/en/product-facts-which-strains-of-bacteria/

- vivomixx  ->  dsm24730+dsm24731+dsm24732+dsm24733+dsm24734+dsm24735+dsm24736+dsm24737
  Why: Vivomixx is the European brand name of that exact eight-strain set (same label as above).
  Source: the Vivomixx strain list quoted above — https://dsf.vivomixx.eu/en/product-facts-which-strains-of-bacteria/

- visbiome  ->  dsm24730+dsm24731+dsm24732+dsm24733+dsm24734+dsm24735+dsm24736+dsm24737
  Why: Visbiome is the US brand name of the same eight strains, under the DSM numbers.
  Source: "L. paracasei DSM 24733/SD5218, L. plantarum DSM 24730/SD5209, L. acidophilus DSM 24735/SD5212, L. delbrueckii subspecies bulgaricus DSM 24734/SD5210, B. longum DSM 24736/SD5219, B. infantis DSM 24737/SD5220, B. breve DSM 24732/SD5206, S. thermophilus DSM 24731/SD5207" and "previously known as VSL#3 and sold by VSL Pharmaceuticals before June 2016 … now exclusively manufactured for ExeGi Pharma and sold under the brand name, Visbiome" — https://ibsprobiotics.org/probiotics/de-simone/
  Peer-reviewed backing: "The current product known as VSL#3 is not the same formulation as the De Simone Formulation or the pre-2016 VSL#3" and the De Simone Formulation "is available under the brand names Visbiome (USA) and CDS22-formula (Europe)" — PMC12852498 (ESNM/UEG consensus correction), https://pmc.ncbi.nlm.nih.gov/articles/PMC12852498/

**Nothing joins to `vsl3` as that key stands today.** See the next two sections.

## Joins I suspect but could not prove

- dsfformulation  ->  dsm24730+dsm24731+dsm24732+dsm24733+dsm24734+dsm24735+dsm24736+dsm24737
  what is missing: the strain list. PMID 40833338 calls the product "DSF Formulation®" and says only
  "a high-dose multistrain probiotic formulation" with eight strains. "DSF" is the standard
  abbreviation of "De Simone Formulation", the trial is Italian, and the dose profile matches, so
  this is very likely the same product — but the abstract never names a single strain and I could
  not reach the full text, and I could not find a maker's page for a product branded exactly
  "DSF Formulation®". I will not join a blend on the strength of an abbreviation.
  What would settle it: the paper's Methods section, or a product page listing DSF Formulation®'s
  eight strains.
  Note: this record scores nothing today (sleep = not_counted, "not_measured"), so the join only
  changes the trial count, not any result.

- 25092036 (the older of the two `vsl3` records)  ->  dsm24730+dsm24731+dsm24732+dsm24733+dsm24734+dsm24735+dsm24736+dsm24737
  what is missing: nothing about the product — the dating is solid (see below) — but this is a
  **record-level** move, not a key-level alias, and `aliases.json` cannot split one key into two.
  The main session has to change the record itself. Details under "Record problems".

## Not the same entity, although they look alike

- vsl3 (PMID 34681287)  vs  dsm24730+…+dsm24737   why: this is the post-split VSL#3, a different
  product made by a different company from different strains.
  What happened, with dates:
  * Claudio De Simone terminated the Know-How Agreement; VSL Pharmaceuticals lost access to the
    real formulation after **January 2016**, and its licence expired in **May 2016**. From then on
    VSL Pharmaceuticals made its own version in Italy.
    Source: "When the VSL Parties lost access to the De Simone Formulation after January 2016 and
    began to manufacture their own version in Italy using a different formulation" — De Simone v.
    VSL Pharmaceuticals, https://www.courtlistener.com/opinion/9737382/de-simone-v-vsl-pharmaceuticals-inc/
  * A federal jury found for De Simone and ExeGi in **November 2018** (over $18 million), and the
    4th Circuit upheld it in **February 2021**, holding the jury could find the VSL parties had
    "reverse-engineered an imperfect copy" of the formulation.
    Source: https://en.wikipedia.org/wiki/De_Simone_Formulation
  * A peer-reviewed correction states it plainly: "The current product known as VSL#3 is not the
    same formulation as the De Simone Formulation or the pre-2016 VSL#3." — PMC12852498,
    https://pmc.ncbi.nlm.nih.gov/articles/PMC12852498/
  Which side PMID 34681287 falls on, with the **trial** dates, not the publication year:
    the trial (NCT04256785, Universidad de Granada) ran from **11 May 2018 to 31 May 2020**
    (actual start and actual completion), entirely after the split, and its industry collaborators
    were **Actial Farmaceutica S.r.l.** and **Ferring Pharmaceuticals** — the Italian maker and the
    European distributor of the *post-2016* VSL#3, not ExeGi.
    Source: https://clinicaltrials.gov/study/NCT04256785 (ClinicalTrials.gov API v2, statusModule
    and sponsorCollaboratorsModule). The paper's own conflict statement agrees: "F.R.V. received
    consultancy fees from Ferring SAU" — PMID 34681287.
  So PMID 34681287 belongs **on its own**: not with Vivomixx/Visbiome, and not with the other
  VSL#3 record.

- oxxyslab  vs  dsm24730+…+dsm24737   why: a different eight strains, from a different company.
  Oxxyslab is SLAB51 / Sivomixx, whose strains are "Streptococcus thermophilus DSM 32245,
  Bifidobacterium lactis DSM 32246, Bifidobacterium lactis DSM 32247, Lactobacillus acidophilus
  DSM 32241, Lactobacillus helveticus DSM 32242, Lactobacillus paracasei DSM 32243, Lactobacillus
  plantarum DSM 32244, Lactobacillus brevis DSM 27961", made by Ormendes SA (Switzerland).
  Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC6405091/
  Every DSM number differs, and the species themselves differ: SLAB51 has L. helveticus and
  L. brevis, which the De Simone Formulation does not, and it lacks B. longum, B. infantis and
  L. delbrueckii subsp. bulgaricus. The catalogue's own record is consistent: NCT06552806 is titled
  "The Effect of a Multi-strain Probiotic SLAB51 (Sivomixx800®) on Acclimatization to High Altitude"
  and lists "Oxxyslab" as the intervention's other name — https://clinicaltrials.gov/study/NCT06552806
  Leave `oxxyslab` as its own key. (Do not be misled by the Vivomixx site's note that its own
  B. longum and B. infantis are now reclassified as *B. lactis*: that is a renaming of the De Simone
  strains, and their deposit numbers are unchanged. It does not make them SLAB51's B. lactis.)

## Record problems (not aliases)

- **PMID 25092036 — the `vsl3` key holds two different products and must be split.**
  This trial is the pre-split, real De Simone Formulation. The paper (Dig Dis Sci 2015;60:186-94,
  online 5 Aug 2014) is the NUH Singapore VSL#3 IBS mechanism study; the matching registration,
  NCT00786123 ("Exploring the Mechanism of a Probiotic Combination VSL#3 in Irritable Bowel
  Syndrome", National University Hospital Singapore, senior author Khek Yu Ho, 4 capsules daily for
  6 weeks — the paper's own 42 patients, 6 weeks, same institution and author), ran from
  **May 2006 to December 2009**. Source: https://clinicaltrials.gov/study/NCT00786123
  Even without that registration the publication date alone puts the trial years before the
  January-to-May 2016 split, so the product can only have been the De Simone Formulation.
  Suggested fix: give record 25092036 the eight DSM strain codes (or a brand that maps to the
  De Simone key), so it pools with Vivomixx/Visbiome; and leave record 34681287 under a key of its
  own — ideally renamed to something unambiguous such as `vsl3post2016`, so nobody later joins it
  to the De Simone family by its brand name. I am fairly but not completely sure that 25092036 is
  NCT00786123, because the paper is paywalled and gives no registration number; the date argument
  does not depend on that identification.
  This cannot be done in `aliases.json`, which only maps key to key. A single alias on `vsl3` would
  merge the reverse-engineered 2018-2020 product into the De Simone row — exactly the worst error
  the brief warns about.

- **PMID 39047340** records the Visbiome arm as "Lactobacillus, Bifidobacterium and Streptococcus
  species" with no strain codes. The brand is enough to key it, but adding the eight DSM codes would
  make it self-evident. Same for PMID 35513910 ("Vivomixx (multi-strain)") and PMID 42068795.

## Could not find out

- The exact strain list of "DSF Formulation®" as used in PMID 40833338. I read the PubMed abstract
  in full (no strains named), searched for a maker's page for that exact trademark, and searched the
  De Simone Formulation literature. The full text (doi 10.1177/17103568251367725) is behind a
  paywall and I did not attempt to bypass it.
- A single primary document (a deposit certificate or a peer-reviewed paper) that states the
  DSM 2473x ↔ NCIMB 3043x equivalence. The pairing above comes from product labels, which list both
  numbers for all eight strains one-to-one and agree with each other across two independent sites.
  I consider that sufficient, but it is label evidence, not a collection record.
