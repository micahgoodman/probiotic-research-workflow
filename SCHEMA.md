# Probiotic Evidence Catalogue — Schema

A strain-level catalogue of what the research actually shows about the health effects of
consumer probiotic preparations — live and non-viable alike — built so that every claim
carries its own evidence strength and traces back to specific studies.

## Row grain

**One row per claim, where a claim is `entity × impact × population`.**

`population` is one of exactly three values: `humans`, `animals`, `in_vitro`.

A strain with human evidence on IBS, AAD, and depression, plus mouse data on IBS and on gut
barrier function, is five rows: three `humans` rows and two `animals` rows — one of which
shares its `impact_id` with a human row and is separated from it only by `population`.

Within an entity, `(impact_id, population)` must be unique — no two claims may share both.
That constraint is what makes "a concise, deduplicated list of impacts" enforceable rather
than aspirational: dedup becomes a check the build step runs, not a judgment call made
differently by every research pass. The unit is the entity, not the file — an entity
researched in several passes is stored across several files, and the guarantee has to hold
across all of them. See Sharding.

Never pack multiple impacts into one cell.

A `humans` row and an `animals` row for the same impact may both exist. Human evidence
does not suppress the preclinical row, and preclinical evidence never feeds the human
one — they are separate ladders. The readable view groups them under a single impact
heading so this reads as one finding with two evidence bases rather than as a duplicate.

When one impact's human evidence spans populations too different to share a description —
hospitalized adults and colicky infants both feeding `mech-microbiome-composition` — the
grain still allows exactly one `humans` row, and that is the convention, not a squeeze:
one row, the best-fit `direction` and `consistency`, each population and which way it
went named in `population_detail` and `tier_rationale`, with tier rule 5 governing a
genuine divergence. The grain is deliberately not widened for this case. A
per-population axis would let the same trial appear under two rows, and double-counting
is the failure the grain exists to prevent; a strained `consistency: mixed` narrated in
prose is the honest rendering of a literature that really is that mixed.

## Storage

| Layer | Path | Role |
|---|---|---|
| Roster | `roster.json` | The entities to research, each carrying the source that put it there. Rebuilt by the sweeps in Roster assembly, not hand-maintained. Also the only home for entity identity — see Fields. |
| Triage output | `triage.json` | Per-entity literature volume and depth budget. Appended to by each triage pass through `tools/triage.py`, consumed by the research stage. See Triage below. |
| Source of truth | `strains/<strain_id>/<shard>.json` | One directory per entity, one file per research pass. See Sharding. |
| Compiled table | `build/catalogue.csv` | Long format, one row per claim. For sorting/filtering/analysis. |
| Readable view | `build/catalogue.md` | Grouped by entity, then by impact, with `humans` / `animals` / `in_vitro` as separate lines beneath each impact heading. The "what does this strain do" view. |
| Coverage report | `build/coverage.md` | Which roster entities have been researched, which shards are missing, and which came back with no claims. Answers "is the catalogue done?" without opening every directory. |
| Shard template | `templates/shard.json` | Annotated skeleton for one research pass, with a worked example per branch of the schema. Kept outside `strains/` so it can never be read as data. |

Never hand-edit files in `build/` — they are regenerated from `strains/`.

### Sharding

A `deep` entity is researched one outcome area at a time (see Triage), so several passes
write to the same entity. A single JSON file per entity cannot absorb that — concurrent
passes clobber each other — so **the unit of storage is the pass, not the entity**:

```
strains/lacticaseibacillus-rhamnosus-gg/     strains/bifidobacterium-breve-bif195/
  gi.json                                      all.json
  immune.json
  mechanistic.json
  safety.json
```

Each shard declares in `body_systems` what its pass covered, and the filename follows from
that declaration: `all.json` when one pass covered all six systems, otherwise `gi`,
`immune`, `metabolic`, `mental-health`, `mechanistic`, or `safety`.

**A claim goes in the shard that owns its impact's body system** — `gi-ibs-global` in
`gi.json`, `mech-gut-barrier` in `mechanistic.json`. Since `impact_id`s are body-system
scoped and each system is owned by exactly one shard, two passes cannot produce the same
claim. The dedup guarantee survives being split across files because collisions are
impossible to write, not merely caught afterward: validation rule 11 checks placement, and
rule 1 checks uniqueness across the whole directory.

The corollary is that a GI pass which stumbles on a gut-barrier mouse study records
nothing. The mechanistic pass finds the same paper, because that is precisely what it is
searching for. Nothing is lost, and no pass ever writes outside its own file.

A pass **always** writes its shard, including when it finds nothing gradeable —
`claims: []` with a `pass_summary` saying what was searched and came back empty. A missing
shard therefore means the pass has not run. This is the same distinction the catalogue
already draws between "not yet considered" and "considered and excluded" for outcomes and
for entities, applied to research passes; `build/coverage.md` is where it becomes visible.

### What makes a pass done

A shard on disk says the pass ran; `searched_empty` says how far it looked. Together with
the claims, the two give every id the pass's body systems allow one of three states:
**claimed** (a row exists), **searched empty** (someone looked and no row could be
written), or **unaccounted**.

- A **deep** pass owes a targeted search for every allowed id, so an unaccounted id is
  debt: the pass counts as unfinished, the entity reads `in_progress`, and
  `tools/plan.py` re-opens exactly that remainder. The debt is derived — allowed minus
  claimed minus `searched_empty` — never declared, so forgetting to record a search
  enlarges the visible debt instead of silently claiming coverage, and an id added to
  the vocabulary after the pass ran re-opens the pass that owns it by plain arithmetic.
- A **standard** or **light** pass owes its known-for areas plus a general sweep, not a
  search per id. Its unaccounted ids are the sweep's normal remainder:
  `build/coverage.md` counts them, and nothing re-opens.

None of this is validated — a half-finished pass is a normal intermediate state — so it
is reported by `build/coverage.md` instead. Only the field's shape is checked: every
entry a vocabulary id within the shard's systems, listed once, and not contradicting a
claim in the same shard.

## Fields

### Identity — in `roster.json` only

Identity lives in `roster.json` and is joined into the build on `strain_id`. A shard
carries `strain_id` and nothing else about the entity, for the same reason a claim row
carries only `impact_id`. Copying identity into each of the four shards of one deep entity
would multiply the drift problem rather than avoid it, and sharding is what turns a
tolerable duplication into an untenable one.

| Field | Contents |
|---|---|
| `strain_id` | Canonical slug, e.g. `lacticaseibacillus-rhamnosus-gg`. Stable primary key, and the only identity field a shard repeats. |
| `entity_type` | `single_strain`, `product`, or `species_level` — a strain, a named commercial formulation, or a species-level culture definition. The axis is *what unit the evidence attaches to*, not what the label says: LGG sold as Culturelle is `single_strain`, because the trials are LGG trials. See Roster assembly for when `product` and `species_level` are permitted. |
| `preparation` | `live`, `non_viable`, or `mixed`. Non-viable preparations are in scope (see Scope) and this field is what keeps them visible: a heat-killed product and a live one are not clinically interchangeable, and the label on the box rarely makes the difference obvious. `mixed` exists because a real product needed it — Neuralli Mood is live PS128 plus heat-treated PS23 — and forcing it into either bucket would have been a false statement about what a buyer swallows. |
| `genus` | Current (post-2020) taxonomy, e.g. `Lacticaseibacillus`. `multiple` for products. |
| `species` | e.g. `rhamnosus`. `multiple` for products. |
| `strain_designation` | `GG (ATCC 53103)`, `DSM 17938`, `BB-12`, or the product name. For `species_level`, the definition the evidence actually used, e.g. `live yogurt cultures (≥10⁸ CFU/g)`. |
| `also_known_as` | Legacy taxonomy names **and** commercial names. Both are required — the 2020 split of *Lactobacillus* into 25 genera means literature searches miss half the corpus without the old name. |
| `component_strains` | `product` only: the composition, as far as it is disclosed. Where a manufacturer withholds a designation, record that rather than leaving the list empty — `Saccharomyces cerevisiae (proprietary strain, designation not disclosed)` is the true and complete answer for EpiCor. Empty for `species_level`, which has no fixed membership; that is the entire reason it needs its own type. |
| `known_for` | One line, a search starting point for triage. **Not an evidence summary** — see Triage for why the difference matters. |
| `roster_source` | Which sweep and which source put this entity here. See Roster assembly. |

### The shard

| Field | Contents |
|---|---|
| `strain_id` | Join key into `roster.json`. |
| `body_systems` | The systems this pass covered. Fixes the filename and gates which impacts may appear in the file — validation rule 11. |
| `last_reviewed` | `YYYY-MM-DD` for **this pass**, and a real date — validation rule 14. An entity's review date is the *oldest* of its shards, so a partially refreshed entity reads stale rather than fresh. |
| `pass_summary` | 2–4 sentences on what this pass covered: best-supported findings, where the evidence is weakest, any safety signal worth knowing. Scoped to the pass — for a single-shard entity that makes it the entity summary; for a deep one, `build/catalogue.md` shows the shards in order. Nothing here may depend on a sibling shard, which is what keeps passes independent — except in the safety pass, the entity's closing pass, which runs after its siblings and reads them: harm signals surface inside efficacy trials, so the harm picture is a synthesis of what the clinical passes found plus its own search. See Triage, depth budgets. |
| `claims` | The rows. See below. |
| `proposed_impacts` | Outcomes with no matching vocabulary ID — see Controlled vocabulary. |
| `searched_empty` | Impact ids this pass individually searched and could not write a row for — the id-level version of the empty pass, so an absent row for a listed id means someone looked. For a deep pass, what it does *not* account for is derived debt — see "What makes a pass done". Shape-checked: vocabulary ids within this shard's systems, listed once, never also claimed here. |
| `gaps` | Optional narrative: why a `searched_empty` id came back empty, notable questions found unstudied, trials underway. |

### The claim

| Field | Contents |
|---|---|
| `impact_id` | Key from `vocabulary/outcomes.json`. **Never invent one** — see Controlled vocabulary below. The row stores only this key; the display label and body system are joined from the vocabulary at build time and are deliberately *not* copied into the row. |
| `direction` | `benefit`, `no effect`, or `harm`. Exactly one value per row — see tier rule 5 for what to do when sub-populations diverge. |
| `population` | `humans`, `animals`, or `in_vitro`. The grain axis, and what enforces the human/non-human separation. |
| `population_detail` | *Who was studied*, free text: `adults with IBS (Rome IV)`, `preterm infants <32wk`, `children receiving antibiotics`, `C57BL/6 mice`. Effects rarely generalize across populations, so a claim without this is unfalsifiable. Not a grain axis — it scopes the row rather than splitting it, and it is where a sub-population split gets named. |
| `study_type` | Array of every study type behind the row, in canonical strongest-first order: `human_meta`, `human_rct`, `human_observational`, `human_case_report`, `animal`, `in_vitro`. The first element is therefore always the unit the tier was graded from. **List a type only when it contributes evidence not already subsumed by a higher one** — a systematic review covering five RCTs is `["human_meta"]`, not `["human_meta", "human_rct"]`; it becomes the latter only when trials exist outside that review's coverage. Without this rule the field is uninterpretable, because `human_rct` would mean both "there are trials beyond the SR" and "the SR contains trials." Must agree with `population` — see Validation rules. |

### Evidence strength

| Field | Contents |
|---|---|
| `evidence_tier` | `A`, `B`, `C`, `D`, or `P`. See below. |
| `n_studies` | Number of independent trials behind the claim — **all of them**, including any that fall outside the coverage of the review named in `effect_size`. `null` when unknown, never `0`. |
| `n_participants` | Pooled N (or animals) across those same trials. `null` when unknown. |
| `independently_replicated` | `yes` / `no` / `unclear` — replication by a *different research group*, not merely more papers from the same one. |
| `consistency` | `consistent`, `mixed`, `conflicting`. |
| `effect_size` | Native units plus CI: `RR 0.57 [0.41–0.78]`, `IBS-SSS −45 points`. It comes from `study_type[0]`, the grading unit. When that unit covers less than all the evidence behind the row — a review of 8 trials on a row that also carries 2 later ones — say so: `RR 0.57 [0.41–0.78] (SR, 8 of 10 trials)`. Otherwise the effect and the counts silently describe different sets of studies. |
| `bias_assessment` | `sr_assessed` (a systematic review formally assessed risk of bias) or `not_assessed` (no SR available; graded from abstracts without independent bias appraisal). Makes the central limitation of abstract-level sourcing filterable rather than invisible. See Source policy. |
| `industry_funded` | `all`, `some`, `none`, `unclear`. Manufacturer sponsorship is unusually prevalent in this literature and correlates with positive findings, so it gets its own filterable field rather than a note. Expect `unclear` often under abstract-level sourcing — see Source policy for how that interacts with tiering. |
| `tier_rationale` | One line: what was downgraded or upgraded and why, and — where they exist — which sub-populations diverged. Makes the tier auditable instead of a vibe. |

### Practical

| Field | Contents |
|---|---|
| `dose` | CFU/day at which the effect was observed, as a range when the row aggregates trials that used different doses: `1×10⁹–2×10¹⁰ CFU/day`. Narrow it to the effective range where the evidence supports one, and say so in `tier_rationale`. Effects vary across orders of magnitude, so a claim without dose isn't actionable — and a single figure invented to stand in for a range is worse than the range. |
| `duration` | Intervention length. |
| `delivery_format` | `capsule`, `sachet`, `fermented milk`, `yogurt`, `drops`. |
| `safety_flags` | Contraindications and adverse events relevant to this claim's population. |

### Provenance

| Field | Contents |
|---|---|
| `sources` | PMID / DOI / URL. Prefer a meta-analysis or systematic review; otherwise the landmark trial(s). |
| `last_reviewed` | Not a claim field — it lives on the shard, because the unit that was reviewed is the pass. See The shard. Listed here only so its absence from the row is a decision rather than an omission. |
| `notes` | Only what genuinely doesn't fit a field above. Not a dumping ground. |

## Evidence tiers

| Tier | Meaning |
|---|---|
| **A — High** | A systematic review or meta-analysis of RCTs, reporting consistent direction and adequate pooled power, with risk of bias formally assessed. |
| **B — Moderate** | ≥2 independent RCTs, or one large well-conducted RCT, without an SR to appraise them — or an SR with limitations (some inconsistency, wholly industry-funded evidence base, modest pooled N). |
| **C — Low** | One small RCT, several pilot/open-label trials, human observational data only, or a meta-analysis with high heterogeneity. |
| **D — Very low** | Uncontrolled studies, case series or case reports (`human_case_report`), or serious risk of bias. Most human safety signals live here — bacteremia and fungemia are documented almost entirely through case reports. |
| **P — Preclinical** | Animal or in vitro evidence. Every `animals` and `in_vitro` row is tier `P` by definition, so within preclinical work the strength signal lives in `n_studies`, `consistency`, and `independently_replicated` rather than in the tier. |

Six rules that make the tiers mean something:

1. **P never upgrades a human tier.** Human tiers are assigned from human evidence alone.
   Mouse data plus one small trial is `C`, not `B`. Preclinical and clinical are separate
   ladders, which is also how the humans/animals separation is enforced — `population` is
   what splits the views.
2. **Composite entities are never decomposed, and never composed either.** Evidence
   belongs to the entity that was actually tested. If Visbiome works for pouchitis, that
   evidence belongs to Visbiome, not to any component strain — do not create a
   *L. plantarum* row from a Visbiome trial. The same holds in both directions for
   `species_level` entities: the yogurt-cultures lactose finding does not become a claim
   about any particular *L. bulgaricus* strain, and a trial of one named strain does not
   become evidence for the species-level entity. Without this the same study would be
   counted twice under two entities and the catalogue would overstate itself.
3. **Tier reflects evidence quality, not effect size.** A well-replicated finding of a
   tiny effect is still tier A; record the smallness in `effect_size`.
4. **Tier A requires a systematic review or meta-analysis.** This follows from
   abstract-level sourcing — see Source policy. A claim resting on individual RCTs whose
   risk of bias nobody has appraised caps at `B`, however many trials there are.
5. **A sub-population split is recorded inside the row, not spread across rows.** Human
   evidence often diverges by sub-population — AAD prevention is well supported in
   children and thinner in adults. The grain still gives exactly one `humans` row, and it
   gets resolved one of two ways — never by silence.

   *Scope the row.* `population_detail` names the sub-population the claim holds in, and
   `direction`, `evidence_tier`, and `consistency` all describe that sub-population's
   evidence — so a tier A finding in children stays tier A.

   *Or state it generally.* `direction` takes the finding from the population where the
   evidence is strongest, ties broken by pooled N; `consistency` becomes `mixed` (one
   population positive, another null) or `conflicting` (opposite directions); and the row
   is **downgraded one tier for indirectness**, since a claim asserted across populations
   when it only holds in one is less certain than the sub-population figure implies.

   Either way `tier_rationale` must name which population went which way and at what
   strength. Silence about a null in half the studied population is the failure mode this
   rule exists to prevent.

6. **A pooled multi-strain estimate is not evidence for any strain in the pool.** Most
   systematic reviews in this field pool at genus or species level rather than by strain —
   that is what Sweep B found, recorded in `roster.json` under
   `_assembly.sweep_b_limitation` — so this is the routine case, not an edge case.
   "*Lactobacillus* for AAD, RR 0.60," across twelve trials of eight strains, is not an LGG
   finding however convenient the citation. Rule 2 forbids decomposing a composite
   *entity*; this forbids decomposing a pooled *analysis*, which is the same error in a
   shape rule 2 doesn't reach. Three cases:

   | The review reports | Grade the row from | `study_type` | Ceiling |
   |---|---|---|---|
   | A strain-specific subgroup estimate | that subgroup | `["human_meta"]` | `A` |
   | Pooled only, but the strain's own trials are identifiable in the included-studies table with their risk-of-bias ratings | those trials | `["human_rct"]` | `B` |
   | Pooled only, strain not separable | — | — | no row |

   The middle case still records `bias_assessment: sr_assessed`, because bias genuinely was
   appraised — and validation rule 6 caps it at `B` anyway, since `human_meta` is absent.
   The consequence to expect from all of this: **tier `A` will be considerably rarer than
   the tier table makes it sound.** That is an honest picture of the literature, not a
   defect in the grading.

## Scope

**Benefits, nulls, and harms all belong in the catalogue.** A well-run trial showing *no
effect* for a widely marketed claim is among the most decision-relevant things the table
can contain, and a catalogue of only positives would function as a publication-bias
amplifier. Harms matter for the same reason: probiotics have caused bacteremia and
fungemia in immunocompromised, central-line, and short-gut patients, and the PROPATRIA
trial found excess mortality in severe acute pancreatitis.

Record everything found and let `evidence_tier` do the filtering, rather than
pre-screening for "good studies" — pre-filtering bakes the judgment in invisibly and
makes it impossible to audit later.

Entity scope is **consumer-available strains and products** — the ones a person can buy
without a prescription, that have real trial evidence. Prescription and physician-
administered live biotherapeutics are out: Rebyota (fecal microbiota, live-jslm) and Vowst
(fecal microbiota spores, live-brpk) are FDA-approved for recurrent *C. difficile* on
phase 3 evidence, and are excluded on availability, not on evidence. Because that
exclusion removes the strongest evidence in the field for one in-scope outcome, it is
recorded in `roster.json` under `excluded_entities` rather than left implicit — a reader
looking at `gi-cdiff-prevention` should be able to see that the approved therapies were
considered and ruled out, not overlooked. Roster in `roster.json`; how it is built is in
Roster assembly.

**Non-viable preparations are in scope.** ISAPP defines a probiotic as a *live*
microorganism, so pasteurized *Akkermansia muciniphila* MucT and heat-killed *Lactococcus
lactis* strain Plasma are postbiotics, not probiotics. They are included anyway. The
catalogue's question is what the evidence shows about the preparations a person can
actually buy, and someone reaching for an immune supplement is not sorting the shelf by
cell viability. Drawing the line at viability would also have cut several of the
better-evidenced Japanese entries while keeping weaker live ones — a scope boundary set by
definition rather than by evidence. Every entity carries `preparation`, so the distinction
stays visible and filterable rather than dissolving into the roster.

The decision widened the roster, and a targeted sweep has since closed the gap it opened —
12 entities added, and one already on the roster reclassified. See Roster assembly. The
finding worth carrying forward is *why* the original sweeps found none of them: the
AEProbio guides, Sweep A's richest source, contain no heat-killed, inactivated, or
pasteurized entries at all. They are probiotic-only by construction. The gap was structural
rather than an oversight, which is the kind of blindness a source list cannot report about
itself.

Body-system scope is **`GI`, `Immune`, `Metabolic`, `Mental health`, `Mechanistic`, and
`Safety`.** Skin, Oral, Respiratory, and Urogenital outcomes are deliberately excluded. A
research pass that finds evidence in an excluded system records nothing — and specifically
does *not* raise it in `proposed_impacts`, which exists for outcomes the vocabulary is
missing, not for outcomes it has ruled out. The excluded IDs stay in
`vocabulary/outcomes.json` under `excluded_outcomes` so that "not yet considered" and
"considered and excluded" remain distinguishable.

This cuts less respiratory evidence than it sounds like. Respiratory-tract *infection*
outcomes are classified `Immune` and remain in scope — `imm-urti-incidence`,
`imm-urti-duration`, `imm-influenza-like`, `imm-vap`, `imm-allergic-rhinitis`. Only asthma
and wheeze prevention leaves with the Respiratory system.

## Roster assembly

The roster is a research output, not a hand-maintained list. A list assembled from recall
has no completeness criterion — you can never answer "are we done?", and its failure mode
is **brand salience**: entities earn their place by being recognizable products in Western
supplement markets, which is not the same test as having trial evidence. That method
missed *L. delbrueckii* subsp. *bulgaricus* OLL1073R-1 and *B. longum* BB536 entirely,
both of which carry substantial human trial bases in Japan.

### Inclusion criteria

An entity belongs on the roster if **all four** hold. These are testable so that a roster
decision is checkable by someone who didn't make it.

1. **Identifiable.** A specific strain designation, a named commercial product, or — see
   below — a species-level culture definition the evidence itself uses. A product qualifies
   even when its composition is undisclosed; a trial that never said what it administered
   does not.
2. **Consumer-available** in at least one of US, Canada, EU, UK, or Japan, without a
   prescription.
3. **Evidenced.** At least one human trial on an in-scope outcome, *or* a documented human
   safety signal. Preclinical work alone is never sufficient for roster inclusion, though
   it is recorded once an entity is on for another reason.
4. **Distinct.** Not the same organism *in the same preparation* as an existing entry
   under a different commercial or legacy name.

**Preparation is part of identity, not an annotation on it.** Criterion 4 is assessed on
strain *and* `preparation`, so the same strain in two preparations is two entities. The
roster carries *B. bifidum* MIMBb75 twice: the live strain, and heat-inactivated
HI-MIMBb75 sold as Kijimea IBS Pro. They are different products with different trials —
the 443-patient Lancet Gastroenterology & Hepatology result is heat-inactivated evidence,
and treating the pair as one entity would attribute it to the live strain. This was not
foreseen when `preparation` was added; the non-viable sweep found it.

Criterion 3 is the one that keeps the roster honest, and it is also why triage cannot be
skipped: at assembly time the answer is often "probably," and triage is what converts that
to a confirmed yes or a `drop` with the reason recorded.

### When `product` is permitted, and when a missing designation disqualifies

`product` is for entities whose evidence attaches to a named formulation rather than to any
organism inside it. Component count is irrelevant — the type was originally called
`multi_strain_product`, which described the common case rather than the actual rule.
EpiCor, a dried *S. cerevisiae* fermentate with one undisclosed strain, is as much a
`product` as Visbiome is with eight named ones. In both, tier rule 2 does the work: no
EpiCor trial may become an *S. cerevisiae* claim.

An undisclosed composition is therefore not automatically disqualifying — but the reason it
is undisclosed decides the question:

| Situation | Verdict | Why |
|---|---|---|
| The composition is a trade secret, the product is the unit a person buys, and every trial administered that product | `product` | The evidence really is product-defined. The secrecy is commercial, not epistemic — knowing the designation would not let anyone buy or reproduce anything different. |
| The composition is unreported because the trial did not say what it administered | **not an entity** | Nothing is identified, so criterion 1 fails and the trial cannot ground a claim about anything. |

The distinction matters for the same reason it does for `species_level` below: a reporting
defect promoted to an entity would launder that defect into an apparent finding. Record the
disclosed part in `component_strains` and the reason in `roster_source`.

### When `species_level` is permitted

Only when **the evidence base is itself species-defined** — not when a trial simply failed
to report which strain it used. The distinction matters because unreported strains are a
reporting defect, and promoting them to species-level entities would launder that defect
into an apparent finding.

The clear case is live yogurt cultures and lactose digestion: EFSA's approved Article 13.1
claim is defined as yogurt containing ≥10⁸ CFU/g of *L. delbrueckii* subsp. *bulgaricus*
and *S. thermophilus*, with no strain designation anywhere in the claim. A strain-only
roster cannot represent the one probiotic health claim in this field with formal
regulatory approval.

Every `species_level` entity must state in `roster_source` why the species is the right
unit. Absent that justification it is a `single_strain` entry with missing information, or
it doesn't belong.

### The two sweeps

Roster assembly runs two independent sweeps and takes their union. They are deliberately
redundant, because each is blind to what the other finds.

**Sweep A — top-down, from source lists.** Enumerable, citable, and re-runnable:

- **AEProbio *Clinical Guide to Probiotic Products*** (US and Canada editions, annual).
  Product × strain × indication × evidence level, rebuilt yearly from a systematic
  PubMed/EMBASE search. The closest thing to a prebuilt version of this roster.
- **WGO Global Guidelines: Probiotics and Prebiotics (2023)**, Tables 8–9 — strain
  designated, evidence graded 1–3, strains without a designation deliberately omitted.
- **Health Canada NHPID probiotics monograph** — permitted strains and their
  strain-specific claims.
- **Manufacturer strain catalogues** — Novonesis/Chr. Hansen, IFF/Danisco (Howaru),
  Lallemand Rosell, Probi, BioGaia, Morinaga, Yakult, Meiji, Sacco, Deerland, Sabinsa.
  This is the step that closes the geographic gap; nothing else will.
- **EFSA QPS list** to bound the species universe; **FDA GRAS notices** for
  strain-designated US entrants.

**Sweep B — bottom-up, from this catalogue's own scope.** For each in-scope clinical
outcome ID, take the most recent systematic review or meta-analysis and enumerate every
strain in its included-studies table.

Sweep B is the one that makes coverage provable, because it matches the scope by
construction: it cannot miss a strain that has evidence for something the catalogue cares
about, brand or no brand. Sweep A finds *commercially* prominent strains; Sweep B finds
*evidentially* prominent ones.

The difference between the two sweeps is diagnostic and worth reading rather than
discarding. In B but not A usually means discontinued, region-locked, or research-only —
check criterion 2 before dropping. In A but not B usually means marketing, and criterion 3
will settle it.

Sweep B targets the outcomes where human trials exist: the GI, Immune, Metabolic, and
Mental health IDs. The 14 `Mechanistic` IDs are skipped deliberately — mechanistic
evidence alone never satisfies criterion 3, so they cannot add an entity that the clinical
outcomes miss. The five `Safety` IDs are swept separately, since safety signals surface
through case reports and pharmacovigilance rather than through meta-analyses.

**Sweep C — non-viable preparations.** Run after the scope decision, because Sweeps A and
B had both completed before it and neither searched for postbiotics as a class. It swept
the Japanese majors, Synformulas/Kijimea, Bened, Chr. Hansen and Maypro against the already
harvested guides. It added 12 entities and reclassified one, and it produced the sharpest
diagnostic yet about Sweep A's sources: **the AEProbio guides list no non-viable
preparations whatsoever.** A source list cannot report its own exclusion criteria, so
sweeping more carefully would never have found these — only changing the question did.

Sweep B has since been completed over the 12 outcome IDs it originally skipped. It yielded
exactly one new entity against eight strains already on the roster, and it re-confirmed
`sweep_b_limitation` more starkly: the blood-pressure, gestational-diabetes, infant-sepsis,
Crohn's-maintenance and radiation-diarrhea reviews name no strain designations at all.
Under tier rule 6 those pooled estimates are evidence for no entity, so several in-scope
outcomes may end up with few or no rows however much literature exists behind them. That is
a real property of the field, and it is better known now than discovered one strain at a
time. Both results are recorded in `roster.json` under `_assembly`.

### Provenance and exclusions

| Field in `roster.json` | Contents |
|---|---|
| `roster_source` | Which sweep and which source put this entity on the roster, e.g. `A: WGO 2023 Table 8` or `B: gi-ibs-global SR`. For `species_level`, also why the species is the right unit. |
| `excluded_entities` | Entities considered and ruled out, each with a `strain_id` and a `reason`. The ID is what lets a later sweep recognize that it has re-proposed something already settled; a free-text label does not survive being written a second time by a different pass. |

`roster_source` is what turns "is the roster complete?" into "was every source swept?",
and it makes a re-run a diff instead of a re-derivation.

`excluded_entities` exists for the same reason `excluded_outcomes` does in
`vocabulary/outcomes.json`: to keep "not yet considered" distinguishable from "considered
and excluded." Without it, a later sweep re-proposes Rebyota, someone re-argues the
prescription question, and the decision gets made twice.

## Source policy

**Grading is done from abstracts, systematic reviews, and meta-analyses.** Full texts are
not required, and a study is never excluded for lacking an accessible full text. When a
full text is accessible — open access, PubMed Central — and the abstract omits a specific
field a row needs, reading it is encouraged: what the policy rules out is a full-text
*requirement*, because the requirement is what would create the bias below.

This is a deliberate trade of depth for coverage. Paywalled and older literature is a
large share of this field, and a full-text requirement would silently bias the catalogue
toward open-access and recent work — a bias that would be invisible in the finished table
and would masquerade as an absence of evidence. Breadth of coverage matters more here than
per-study depth.

What abstracts reliably carry: study design, population, N, intervention and dose,
primary outcome, direction, and — for meta-analyses — pooled effect size with CI, study
count, heterogeneity, and often a publication-bias assessment.

What they often don't: funding source, allocation concealment, blinding integrity,
attrition, and whether the reported primary outcome matches the registered one.

Four consequences, encoded in the fields and rules above:

1. **Risk of bias can't be appraised from an abstract**, so the catalogue defers to
   systematic reviews that did appraise it. Hence tier rule 4: tier A requires an SR or
   meta-analysis. Where an SR exists **and its estimate is attributable to this entity**,
   prefer it as the grading unit over the individual trials it covers — with `study_type`
   this is mechanical, since the SR sorts to `study_type[0]` and the trials it subsumes
   are not listed separately. Where the SR pooled across strains, it is not the grading
   unit and tier rule 6 governs; `bias_assessment` stays `sr_assessed` either way, because
   what it records is whether bias was appraised, not whose estimate was used.
2. **`industry_funded` will frequently be `unclear`.** Record what's visible — PubMed
   grant metadata, funding statements quoted in SR abstracts, and author affiliation with
   the manufacturer all count as evidence. Treat `unclear` as genuinely unknown: it is
   never grounds for a downgrade, and equally never counts as independence for the tier A
   "not wholly industry-funded" consideration.
3. **`effect_size` and `n_participants` may be absent for individual-RCT rows** even
   though they're usually present for meta-analysis rows. Leave them empty — `null` for
   the counts, `""` for `effect_size` — rather than estimating. An empty field is honest,
   an invented one is not, and `0` is neither: it reads as a real measurement.
4. **`dose` and `duration` are often the fields an abstract omits.** Look for them in
   the same read that grades the claim, and in an accessible full text if the abstract
   lacks them. When they are genuinely unreported in what's accessible, write that in
   the field — `"not reported in the sources graded"` — rather than leaving it empty.
   An empty field reads as a pass that never looked, and is what the validator's
   no-dose warning flags; a stated absence is a finding about the literature, and it
   closes the question.

**When more than one systematic review covers the same claim**, grade from the most recent
one with adequate scope and name the others in `tier_rationale`. If two current reviews
disagree in direction, that is not a tie to break: `consistency` becomes `conflicting` and
the row caps at `C`, which is where the tier table already places a body of evidence whose
own reviews can't agree on it.

Never infer an unreported value from a study's design, and never treat a title as an
abstract. If a claim's direction cannot be determined from what's actually accessible, the
claim doesn't go in the catalogue.

## Triage

Roster entities differ enormously in literature depth — LGG and *S. boulardii* have
hundreds of trials and multiple Cochrane reviews; PS128 has a handful of small studies. A
fixed research budget per entity would starve the deep ones and waste effort on the thin
ones.

So research runs in two stages. **Triage** is one cheap pass per entity that estimates the
available literature and assigns a depth budget; the **research** stage then scales its
effort to that budget. Triage writes `triage.json`:

| Field | Contents |
|---|---|
| `strain_id` | Matches `roster.json`. |
| `n_systematic_reviews` | Approximate count of SRs/meta-analyses found. |
| `n_human_trials` | Approximate count of human RCTs found. |
| `has_preclinical_only_areas` | Whether notable claims rest on animal work alone. |
| `outcome_areas` | In-scope body systems where evidence appears to exist — tells the research stage where to look. Excluded systems are never recorded here; note them in `triage_notes` where they bear on the depth call. |
| `depth` | `deep`, `standard`, `light`, or `drop`. |
| `triage_notes` | Anything the research stage should know, including taxonomy or formulation traps. |

Depth budgets:

- **`deep`** — multiple SRs across several outcome areas. One pass per body system in `outcome_areas`, plus a `mechanistic` and a `safety` pass always, each writing its own shard. Those two are separated because they cut across every clinical area: a strain's gut-barrier work and its bacteremia case reports surface while researching GI, Immune, and Metabolic alike, and giving each a single owning pass is what makes a cross-shard duplicate impossible rather than merely detectable. The safety pass is also the one exception to pass independence: it is the entity's **closing pass** — it runs after every sibling is written and reads them, because harm signals surface inside efficacy trials and a safety shard blind to the PROSPECT-style findings sitting in its siblings would be a worse safety shard. Every other pass stays independent, which is what lets a deep entity's clinical and mechanistic passes run in any order, or at once, with safety serialized last.
- **`standard`** — some RCTs, perhaps one SR. Single pass across all outcomes, writing `all.json`.
- **`light`** — few or small trials, or mostly preclinical. Brief single pass, also `all.json`; expect few claims, most at `C`/`D`/`P`.
- **`drop`** — an inclusion criterion fails on inspection: no real trial evidence (criterion 3), all evidence sits in excluded body systems (criterion 3, in scope terms), or the entity isn't distinct from one already on the roster (criterion 4). Move it to `excluded_entities` **keeping its `strain_id`**, with the reason, rather than deleting it — a dropped entity that leaves no trace gets re-proposed by the next sweep, and one that leaves only a label can't be matched against the sweep that re-proposes it.

**A drop is confirmed, never inferred from `known_for`.** That field is a search starting
point, not an evidence summary, and strains routinely have trial evidence their one-line
description omits. This matters most for entities whose place on the roster was earned in
a body system now excluded: GR-1, RC-14, CTV-05, and *S. salivarius* M18 read as entirely
out of scope, while K12 and CECT 5716 keep in-scope evidence — otitis media and URTI,
infant infections respectively — behind an out-of-scope headline. Triage looks for
in-scope evidence in each and records what it found either way, including when the answer
is none.

Triage also owns a second confirmation, created by the sweeps. Nine entities carry
`roster_source: "recall (pre-sweep)"` — ST11, CTV-05, EVC001, 1714, M18, DE111,
Enterogermina, pasteurized *Akkermansia*, and Ecologic 825 — meaning neither sweep
surfaced them. That is a signal, not a verdict: several are simply outside the US, UK,
and Canada consumer markets the guides cover, and one (Enterogermina) is a major product
in Italy and India. Triage confirms criteria 2 and 3 for each and records the answer.
A `recall (pre-sweep)` source is the weakest provenance on the roster, and it is the one
place where "we never checked" and "we checked and it holds" still look the same.

Triage counts are estimates for budgeting only. They are never a source for
`n_studies` or `n_participants`, which come from the research stage.

## Controlled vocabulary

`impact_id` must come from `vocabulary/outcomes.json`. This is what makes deduplication
possible: without it, parallel research passes produce "reduces IBS symptoms," "improves
IBS-SSS," and "relieves abdominal pain in IBS" as three separate rows for one finding.

**The vocabulary is the only place a display label or body system is stored.** A claim row
carries `impact_id` and nothing else about the outcome; `build/catalogue.csv` and
`build/catalogue.md` get `health_impact` and `body_system` by joining on that key. Copying
them into every row would create a second source of truth that drifts — a renamed label
would have to be edited in the vocabulary and in every shard that used it, and a missed
edit would put one outcome under two body systems and silently split the grouped view.
Storing the key once makes that failure unrepresentable instead of merely detectable. The
same reasoning is why identity lives only in `roster.json` — see Fields.

The vocabulary carries a second load under sharding: the body system it assigns to an
`impact_id` is what decides which shard a claim belongs in (validation rule 11), so the
join is not only a display convenience.

The cost is that a shard read raw shows `gi-aad-prevention` rather than "reduces
antibiotic-associated diarrhea." The IDs are legible enough for that, and
`build/catalogue.md` is the intended reading surface.

Use the most specific ID that fits. Several outcomes are already population-scoped —
`gi-acute-diarrhea-children`, `gi-infant-colic`, `gi-nec-prevention` — and a finding in
that population belongs under the specific ID rather than blended into a broader one.

If a genuine outcome has no matching ID, do **not** mint one. Record it in the shard's
`proposed_impacts` array with a suggested label and rationale, for reconciliation into the
vocabulary as a deliberate step. A proposal keeps `suggested_body_system` even though claim
rows carry no body system, because there is no vocabulary row to join one from yet — the
suggestion is the input to writing that row.

Reconciliation needs no follow-up bookkeeping. The moment an id lands in the vocabulary
it is allowed, unclaimed, and unsearched wherever it applies, so the deep pass that owns
it re-opens with exactly that id owed — see "What makes a pass done". Rows for the new id
are then written by a research pass under the normal procedure, never by the
reconciliation step itself; the reconciler clears the proposal and leaves its source
leads in the shard's `gaps` so the pass that re-opens does not start from nothing.

Check `excluded_outcomes` before proposing anything. An outcome listed there is out of
scope by decision, not by oversight, and proposing it generates reconciliation work for a
question already answered.

## Validation rules

Invariants the build step checks. A violation is a defect in the data, not a judgment
call.

1. **`(impact_id, population)` is unique across all shards of an entity.** This is the
   dedup guarantee — see Row grain. The scope is the directory, not the file, because
   sharding splits an entity across several.
2. **`impact_id` exists in `vocabulary/outcomes.json`.**
3. **Directory name matches `strain_id`**, `strain_id` exists in `roster.json`, and each
   shard's filename matches its declared `body_systems` — `all.json` for all six, the
   system's own slug otherwise.
4. **`study_type` agrees with `population`:** a `humans` row carries only `human_*`
   values; an `animals` row is exactly `["animal"]`; an `in_vitro` row is exactly
   `["in_vitro"]`. The field therefore only does real work on human rows.
5. **`study_type` is in canonical strongest-first order** — `human_meta`, `human_rct`,
   `human_observational`, `human_case_report`, `animal`, `in_vitro`. Fixed order keeps the
   compiled CSV column stable across rebuilds (so diffs show real changes, not reordering)
   and guarantees `study_type[0]` is the grading unit.
6. **Tier `A` requires `human_meta` in `study_type` and `bias_assessment: sr_assessed`** —
   tier rules 4 and 6, made checkable.
7. **Tier `P` if and only if `population` is `animals` or `in_vitro`.**
8. **Roster provenance is complete:** every entity carries a non-empty `roster_source`,
   every entry in `excluded_entities` carries a `strain_id`, and no `strain_id` appears in
   both lists. An entity with no recorded source is one nobody can audit, which is the
   failure the sweeps exist to fix — and an exclusion with no ID can only be diffed on
   free text, which defeats the reason exclusions are recorded at all.
9. **`entity_type` is one of `single_strain`, `product`, `species_level`, and
   `component_strains` is non-empty if and only if `entity_type` is `product`.** Catches a
   `species_level` entity that was really a product entry with its component list dropped.
   The `iff` survives an undisclosed composition because the honest entry is a statement,
   not an absence — see Roster assembly.
10. **`preparation` is `live`, `non_viable`, or `mixed`** on every roster entity. All three
    are in scope; none may be left unstated, because they are not clinically
    interchangeable.
11. **Every claim's `impact_id` belongs to a body system its shard declares.** The system
    is joined from the vocabulary — nothing about it is stored on the row. This is what
    makes a misfiled claim, and therefore a cross-shard duplicate, impossible to commit
    quietly.
12. **`n_studies` and `n_participants` are `null` or positive**, never `0`. A zero
    reads as a measured zero — "counted, and there were none" — which is never what a
    claim row asserts: a case-report row has no denominator, and an uncounted total
    is unknown. `null` means unknown and reads as unknown.
13. **`direction`, `consistency`, `independently_replicated` and `industry_funded`
    each carry one of their stated values**, and none may be absent. These are the
    fields the evidence-strength view is built from, and a misspelled `benefits`
    validates cleanly and then disappears from every filter on `benefit` — present in
    the data and absent from every view built on it, which is worse than a row that
    was never written. Absence is ruled out for the same reason: `industry_funded` and
    `independently_replicated` already have a value for "nobody knows," so an empty
    field is silence where the schema provides a word, and a row without `direction`
    asserts nothing at all.
14. **`last_reviewed` is a real `YYYY-MM-DD` date on every shard.** Evidence moves and
    a stale row should be visibly stale, but the placeholder is the sharper problem:
    `YYYY-MM-DD` sorts *after* every real date, so an entity's review date — the
    *oldest* of its shards — would skip the unfinished pass and report the entity as
    fresher than its stalest one, inverting the failure this field exists to prevent.
    `templates/shard.json` is exempt, as it is from the filename rule: it is a
    skeleton rather than a pass, and a real-looking date there would be copied
    verbatim into shards, which is precisely what the loud placeholder prevents.
15. **Every entry in `triage.json` names a `strain_id` that appears exactly once
    there, and on exactly one of `roster.json`'s two lists.** Rule 8's guarantee,
    carried into the stage that consumes it. Triage output commissions research: an
    entry naming nothing on the roster budgets passes for an entity that does not
    exist, and two entries for one entity make the pass plan depend on which the
    reader reaches first. A dropped entity keeps its triage entry and resolves against
    `excluded_entities` — that record is the evidence the drop was confirmed rather
    than inferred.
16. **The vocabulary is a valid join table.** Every entry in `outcomes` carries a
    unique `id`, a usable `label`, and an in-scope `body_system`; every entry in
    `excluded_outcomes` carries an `id`; and no id sits on both lists. Every claim
    resolves through this file, so a defect here never announces itself — it silently
    redefines rules 2 and 11 for every claim that joins through the damaged row. A
    duplicate id is the sharpest case: the last copy wins the join, so a claim filed
    correctly under the first copy's body system starts drawing false rule 11 errors.

Rule 11 validates where a claim sits, not what it stores. A row still carries no body
system of its own, so the defect where one outcome appears under two body systems and
silently splits the grouped view remains impossible to represent rather than merely
detectable.

Rules 13 and 14 are what let the build step stop defending against its own inputs. A
compiled view that had to cope with an unorderable date or an unrecognised `direction`
would be carrying a fallback for a state the validator now makes unreachable, and a
fallback is how a defect becomes a rendering quirk instead of an error.

Two structural checks precede the numbered rules, and block the build exactly as a
rule violation does. A file the loader cannot read as its documented shape is a
**parse** error; a field or entry that does not have its documented type — a claim
that is not an object, a `sources` that is a bare string, a line break inside a
single-line field, a `searched_empty` entry that is not a vocabulary id within the
shard's systems or that contradicts a claim beside it — is a **shape** error. A structure that cannot be read cannot be
validated, only reported: silently coercing it to an empty one would let a destroyed
file validate cleanly, which is the one way a defect becomes invisible.

Checks outside the rules and those two classes are **reported, not enforced**: a
missing `population_detail` or `tier_rationale`, an absent `dose` on a human benefit
row, an unrecognised field name, a triage `depth` or `outcome_areas` value that is
readable but unusable. They go to `build/coverage.md` and never block a build. The
line is whether the defect is representable in a finished catalogue — a row whose
tier nobody justified is thin research, which is a normal intermediate state, while
a row whose `direction` is unreadable is broken data.

Coverage is checked but not validated. Which roster entities have no directory, which
expected shards are missing, which shards returned `claims: []`, and which allowed ids a
written pass has still not accounted for all go to `build/coverage.md` as a report,
because none of them is an invariant — a half-researched catalogue is a normal
intermediate state, not a defect.

The tier rules' requirement that a sub-population split be named in `population_detail`
and `tier_rationale` (tier rule 5) is prose, so it is a review item rather than a machine
check. It is the one place the schema depends on the research pass being honest rather
than on the build step catching it.
