# Availability probe, 18 October 2026: what the five readers reported

Five Sonnet 5.5 readers (effort high), 31 entities each, web search and page fetch only.
Result before review: 155 files, 38 found, 117 none found. After the main session's review
(every found URL fetched again; two records fixed so 155 entities became 154): 38 found,
116 none found. This file keeps the readers' judgement calls and naming notes, because the
chat transcript does not survive the session.

## Fixed by the main session during review
- `ncfm`: the recorded Drogal URL returned 404; replaced with the real Florastor page
  (same shop, R$ 20,99, "Comprar", names "Lactobacillus acidophilus NCFM").
- Three `names` fields re-copied from the page text (OMNi-BiOTiC SR-9, OMNi-BiOTiC Stress
  Repair, NRGBiotic): the readers had re-ordered the lists.
- Records 37571403 (HEAL9 (DSM 15312)) and 37576702 (Lpla33 (DSM34428)) listed a strain's
  deposit number as a second code. One strain, one code: fixed to `HEAL9` and `Lpla33`.
  HEAL9 now pools with the other HEAL9 record.
- The brief said "a price and a way to buy"; rule 8 says "a price or a way to buy". Rule 8
  wins; the brief was corrected. Pages with a buy control and no visible price (m63 at Whole
  Foods, NRGBiotic at Amcal, the two Bened Life pages) count.
- Two Drogal pages (dr7, ncfm) and the DE111 page (kiwla.com, India) were confirmed by a
  second fetch. The DE111 page names only DE111 and shows no ingredients panel.

## Cases rule 8 did not settle (grouped)
1. **Non-strain extras on the page, not in the key.** Zenflore (1714) adds B vitamins; Lactinova
   stres (bb077+pbs072) adds B vitamins; Gasteel Plus (cbp001010+cncmi4036+es1+FOS) adds zinc,
   selenium, vitamin D; Probi Sense (heal9) adds magnesium, zinc, iodine; anatis ExoBDNF
   (exobdnf) adds Triphala and skullcap. Readers split: 1, 3, 4 counted them; reader 2 refused
   (heal9, exobdnf none found).
2. **Non-strain extras in the key, not on the page.** Activia (dn173010+honey): no honey;
   Enterolactis Duo (dg+inulin+vitaminb1/b2/b6): inulin only, the B-vitamin version is a
   different drink; Lactoflorene Plus (…+folicacid+…): folic acid not seen. Reader 5 counted
   them, because rule 8 asks only for codes.
3. **Heat-killed wording.** ANA Mall Dear-Natura CP2305 says 殺菌乳酸菌末 ("sterilized lactic
   acid bacteria powder"), never heat-killed/加熱/死菌/postbiotic. Counted, flagged.
4. **Practitioner or pharmacist gate, no prescription.** UltraBiotic 60 (Fairfield, price and
   Add to cart, labelled practitioner-only) counted; Biome Lift (dsm23233+lf16+lp01+lr06),
   UB NuroBiota (bb06+…+r0175) and Pro4-50 sit behind logins: none found.
5. **Blocked pages (16 entities).** 403 or bot checks at Choice Pharmacy, Nowa Farmacja,
   Apotea, Tesco, Asda, Chemist Warehouse, iHerb, docmorris, drmax, Grisso, Sapporo, JD, Tmall.
   Readers did not bypass; none found with `searched` saying what blocked them. Known products
   behind blocks: NEURO4biotic (bl04+lf16+lp01+lr06), bb536+m16v+m63 blend, Probi Sense
   (heal9, Apotea), Actimel (dn114001), Gynophilus with LCR35 shown (lcr35, out of stock where
   readable), bifico 培菲康 (JD), BC99, SBC8803, WONDERLAB (expired Tmall offer).
6. **Code only in an image** (fb0012+fb0015+fb0047, FitBiomics Nella): none found.
7. **Shop typo in a code** (Simbioflora writes LPC-31 for LPC-37; WONDERLAB page writes BI-04
   for Bl-04): none found.
8. **Brand look-alikes** (lactocare: Danish, Malaysian, Brazilian products share the name;
   target is Zist Takhmir's): none found. **Brand keys with many products** (lactibiane:
   Reference chosen because the trial says four strains; colicron: nine-strain label not
   checked against the trial): counted because the brand is on the page.
9. **Stock contradictions.** Eubiota 12 (sp1) says "Disponibile" and, lower, "Non
   disponibile!"; Welzo Visbiome shows Add to Cart and "Email when stocked"; Triquetra
   (cncmi1079) shows ADD TO CART and NOTIFY ME together; Pasteur Pharmacy pages say "additional
   processing time". All counted. Sold-out pages were treated as not available today
   (299v at Jarrow retailers, dsm17938 at Well.ca, lcasei431, bbr60).
10. **Medical food without prescription** (Neuralli MP, Visbiome): counted.
11. **Country inferred** (lactibiane at MazenOnline: "Lebanon" from the S.a.l. footer and a
    +961 number). **Price read from the shop's product JSON**, not the visible page (both
    Bened Life pages).
12. **Mixed live/heat-treated product.** Neuralli Mood (ps128+ps23) is live PS128 plus
    heat-treated HT-PS23; the record's arm is `live`, so the key has no `heatkilled`. Rule 4
    has one preparation per arm.
13. **Live keys whose only products are heat-killed**: kw3110 (Kirin "KW lactic acid
    bacteria"), snk12 (SNK1000). The records may have the wrong preparation.

## Entities that may be misnamed in the catalogue (notes only, for the second run)
- cncmi1519+cncmi1630+cncmi1631+cncmi1632 (+hypocaloricdiet): these are Danone yogurt starter
  strains (S. thermophilus I-1630, L. lactis I-1631, L. bulgaricus I-1519/I-1632, as in
  Activia), not a "psychobiotic oral suspension". Codes may come from the wrong source.
- moodamin, comflor(+zinc), biozend+vitamind, gh+prebiotics (NEXARS): no product or paper
  outside the trial uses the name.
- bia6+bia7+bia8(+prebiotics)+t16, a6+b09+l9+lp06, p30021+p30025, kabp031+kabp032 (only
  KABP011/012/013 exists), ly66+olp01+pl02, bli02+bv889+cp9+pl02+vdd088 (PL-02 unknown),
  ol3246, k11, cbtlr5: codes unseen outside the trial.
- 2071 is B. breve 207-1 with the dash dropped; 20727 is 207-27 (sold as "LPB27" in a
  Life-Space blend); p8 is "P-8".
- la5+lcasei01: "CASEI-01" unknown; Chr. Hansen's is L. casei 431.
- hu58+sc208: SC208 is called B. coagulans elsewhere, not "Heyndrickxia faecalis".
- lactofem: the trial's product does not match the Lactofem products on sale.
- dg+inulin+vitaminb1+vitaminb2+vitaminb6 may mix two Enterolactis products.
- b3+bb536+m16v+m63: BB536+M-16V+M-63 is a known trio; B-3 is from another Morinaga line.
- fb0012+fb0015+fb0047: real Nella strains; trade press also writes FB00015.
- erythromycin+pro450dlactatefreemultistrain: Spectrumceuticals Pro4-50 never says
  "D-lactate free".

## Process notes
- Readers saw prompt-like text in fetched pages (promofarma.com, probi.se) and ignored it.
- Amazon pages are huge; codes sat at character 700,000 (bla80).
- Readers shared one scratchpad helper file by accident; a few early writes failed and were
  redone. All files were re-checked for shape at the end.

## Re-check in Chrome by the main session (18 October 2026, after the rulings)
The user ruled: strains only (non-strain extras ignored both ways); "sterilized"/殺菌 counts as
heat-killed; re-check the eight blocked entities with a named product. Results:
- FOUND: heal9 (Apotea, Sweden, Probi Sense, 127 kr, Köp, 40 in stock); exobdnf (Vitalabo,
  Austria, € 21,51, 5 in stock); bl04+lf16+lp01+lr06 (Nowa Farmacja, Poland, NEURO4biotic,
  29,99 zł, Dodaj do koszyka, Dostępny; page passed its bot check after a wait, nothing was
  bypassed); lcr35 (Dr. Max Romania, Gynophilus Pro oral capsules, 44,99 Lei, Adauga in cos,
  In stoc; same strain, oral, marketed for vaginal flora).
- STILL NONE FOUND: dn114001 (shops print only "L. casei Danone"); bifico and WONDERLAB
  (JD.com login wall); bb536+m16v+m63 (Choice Pharmacy search 404s; no three-strain drops
  found anywhere); bc99 (grissolife.com returns its home page for every product path).
