# Probiotical and AB-Biotics strains sold under two codes

Added 18 October 2026. Each line gives the alias key, the key it joins, and the source
that prints both names for one strain. The surviving key is the one the shop pages use.

## dsm23233 -> bl04 (Probiotical, Bifidobacterium longum)

- PMID 37720373 (PMC10501394), Methods: "Bifidobacterium longum 04 (DSM 23233)".
- PMID 40077722 prints the same product's strain as "B. longum BL04".
- Probiotical patents US 10688138 and US 9833484: "Bifidobacterium longum BL04, DSM 23233".
- Product page (nowafarmacja.pl, NEURO4biotic): "Bifidobacterium longum BL04 (DSM 23233)",
  the page recorded for the entity `bl04+lf16+lp01+lr06` in available.json.

Known limit: IFF sells a *Bifidobacterium lactis* "Bl-04" (HOWARU), a different strain
whose code also normalises to `bl04`. It appears only inside a six-strain blend
(PMID 37497057), so no row merges today. See RULES.md rule 4.

## kabp023 -> cect7485 and kabp052 -> cect7480 (AB-Biotics)

- PMID 39798036 (PMC11845535), Methods: "Lactiplantibacillus plantarum CECT7485 (KABP023)
  and Levilactobacillus brevis CECT7480 (KABP052) in a 1:1 ratio". The KABP code is the
  maker's catalogue name for the deposited strain; the paper prints both for each strain.
