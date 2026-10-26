# Winclove "W-code" multispecies products

Two different Winclove products are involved, and they must not be mixed up:

- **Ecologic BARRIER** (Winclove 818) = W19, W23, W24, W37, W51, W52, W56, W58, W63.
  Polish brand name: **Sanprobi Barrier**.
- **Ecologic 825** = W19, W20, W22, W23, W24, W51, W52, W56, W62.
  Austrian brand name: **OMNi-BiOTiC STRESS Repair**.

They share only W19, W23, W24, W51, W52 and W56. BARRIER adds W37, W58, W63; 825 adds
W20, W22, W62.

## Joins I am confident about

- ecologicbarrier  ->  w19+w23+w24+w37+w51+w52+w56+w58+w63   (the surviving key is the W-code key, because it states the composition rather than a brand name)
  Source: "The multispecies probiotic formulation Ecologic BARRIER was manufactured by Winclove Probiotics (Amsterdam, the Netherlands). It contains 9 bacterial strains (Bifidobacterium bifidum W23, Bifidobacterium lactis W51, Bifidobacterium lactis W52, Lactobacillus acidophilus W37, Lactobacillus brevis W63, Lactobacillus casei W56, Lactobacillus salivarius W24, Lactococcus lactis W19, and Lactococcus lactis W58)." — PMID 39504580 (PMC12597526), Methods, "Investigational Product and Randomization"

- sanprobibarrier  ->  w19+w23+w24+w37+w51+w52+w56+w58+w63   (the surviving key is the W-code key; Sanprobi Barrier is the same nine strains sold in Poland by Sanprobi)
  Source: "Sanprobi Barrier (manufacturer: Sanprobi sp. z o. o. sp. k., Szczecin, Poland), consisting of Bifidobacterium bifidum W23, Bifidobacterium lactis W51, Bifidobacterium lactis W52, Lactobacillus acidophilus W37, Levilactobacillus brevis W63, Lacticaseibacillus casei W56, Ligilactobacillus salivarius W24, Lactococcus lactis W19, and Lactococcus lactis W58" — PMID 38068763 (PMC10707788)
  Note: this is a strain-for-strain match with the Ecologic BARRIER quote above, so the join rests on the composition, not on the brand story. PMID 38068763 is itself already filed under the W-code key.

- omnibioticstressrepair  ->  w19+w20+w22+w23+w24+w51+w52+w56+w62   (the surviving key is the W-code key; OMNi-BiOTiC STRESS Repair is Ecologic 825 under the Austrian Allergosan brand)
  Source: "Ecologic®825 (manufactured by Winclove Probiotics, The Netherlands, commercially available as OmniBiotic® Stress Repair through Institut Allergosan, Austria)" and the strain list "Lactobacillus casei W56, Lactobacillus acidophilus W22, Lactobacillus paracasei W20, Bifidobacterium lactis W51, Lactobacillus salivarius W24, Lactococcus lactis W19, Bifidobacterium lactis W52, Lactobacillus plantarum W62 and Bifidobacterium bifidum W23." — PMID 29723105 (PMC6287679)
  Second source (the maker's own page, same nine strains): "9 bacterial strains ... Lactobacillus casei W56, Lactobacillus acidophilus W22, Lactobacillus paracasei W20, Bifidobacterium lactis W51, Lactobacillus salivarius W24, Lactococcus lactis W19, Bifidobacterium lactis W52, Lactobacillus plantarum W62, Bifidobacterium bifidum W23" — https://www.allergosan.com/en/produkte/omni-biotic-stress-repair/

## Joins I suspect but could not prove

(none)

## Not the same entity, although they look alike

- w19+w23+w24+w37+w51+w52+w56+w58+w63  vs  w19+w20+w22+w23+w24+w51+w52+w56+w62
  why: these are the two different Winclove products above — Ecologic BARRIER and Ecologic 825.
  Six W codes overlap, but BARRIER has W37, W58 and W63 while 825 has W20, W22 and W62.
  Do not merge them, and do not let the brand names cross over: "Barrier" always means the
  first list, "STRESS Repair" always means the second.

- fructooligosaccharides+inulin+vitaminb12+vitaminb2+vitaminb6+w19+w20+w22+w23+w24+w51+w52+w56+w62
  vs  w19+w20+w22+w23+w24+w51+w52+w56+w62
  why: the key with the trailing "9" in its name ("OMNi-BiOTiC STRESS Repair 9", PMID 37233680)
  has the **same nine strains**, but the product also carries B vitamins, which the plain
  STRESS Repair does not. Under rule 4 an added vitamin is part of the key, so these stay
  apart.
  Source (the studied product's full composition): "The composition of 'OMNi-BiOTiC® STRESS Repair 9' is: Corn starch, maltodextrin, inulin, potassium chloride, vegetable protein (rice), 9 human bacterial strains, magnesium sulfate, fructooligosaccharides (FOS), enzymes (amylases), vitamin B2 (riboflavin 5'-sodium phosphate), vitamin B6 (pyridoxine hydrochloride), manganese sulfate, vitamin B12 (cyanocobalamin)." — PMID 37233680 (PMC10221065)
  Source (the plain product has no B vitamins, and a separate vitamin version exists):
  the Allergosan shop page for OMNi-BiOTiC STRESS Repair lists no B vitamins and names a
  separate "OMNi-BiOTiC Stress Repair with B vitamins ... supplemented with vitamins B2, B6
  and B12 for the nerves" — https://shop.omni-biotic.com/en-eu/products/omni-biotic-stress-repair-int-99113
  So the trailing "9" is the vitamin-enriched sibling, not a different strain set.
  There is no `omnibioticstressrepair9` key in entity-keys.txt; that record lives under the
  long FOS+inulin+vitamin key above.

## Record problems (not aliases)

- **PMID 25862297** (Steenbergen 2015, *Brain Behav Immun*), currently keyed
  `w19+w23+w24+w37+w52+w56+w58+w63`. The abstract lists only eight strains — "Bifidobacterium
  bifidum W23, Bifidobacterium lactis W52, Lactobacillus acidophilus W37, Lactobacillus brevis
  W63, Lactobacillus casei W56, Lactobacillus salivarius W24, and Lactococcus lactis (W19 and
  W58)" — with **B. lactis W51 missing**. The product used was Ecologic Barrier, which has
  nine strains including W51 (quote in the first join above). A paper from the same group
  and the same maker lists all nine. The right value is almost certainly
  `w19+w23+w24+w37+w51+w52+w56+w58+w63`, i.e. the same key as the other five records.
  Honest limit: I could not read the full text (Elsevier returned 403 and Europe PMC has no
  open copy), so I confirmed the omission only in the abstract. If the main session can open
  the full text, check the methods paragraph for W51 before folding this record in.

- **PMID 38891799** (Wiącek 2024, dancers, "Sanprobi Stress"), currently keyed
  `rosell17+rosell52`. "Rosell-17" is a truncation of **Rosell-175**, not a real strain name.
  The paper itself writes "Lactobacillus helveticus (Rosell-52) and Bifidobacterium longum
  (Rosell-17)" at 3 x 10^9 CFU per capsule, but Sanprobi Stress is "1 kapsułka zawiera 3 mld
  CFU bakterii probiotycznych: Lactobacillus helveticus Rosell-52 i Bifidobacterium longum
  Rosell-175" — https://www.lekinfo24.pl/lek/Sanprobi-Stress.html — and the other Sanprobi
  Stress record in the catalogue (PMID 38732635) names Rosell-175. The dose matches too.
  The right value is `rosell175+rosell52`. I found no strain-collection record for any
  "Rosell-17". Fix the record rather than adding an alias; if the main session prefers an
  alias, it is `rosell17+rosell52 -> rosell175+rosell52`.

## Could not find out

- Whether the four `omnibioticstressrepair` records and the four `ecologicbarrier` records
  each state the full strain list in their own papers. I checked the brand identity, which is
  enough for the join, but I did not open all eight papers. If any of them turns out to have
  used a vitamin-enriched or reformulated version, that record would need its own key.
