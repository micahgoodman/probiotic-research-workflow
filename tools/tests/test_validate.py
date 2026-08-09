"""Each test breaks one invariant and asserts the rule that exists to catch it fires.

A validator nobody has tried to fool is a validator nobody knows works. The
docstrings say what each rule is protecting, because a test that only records
"rule 7 fires" stops being a reason to keep rule 7 the moment someone questions it.
"""

from __future__ import annotations

import contextlib
import io
import unittest

from fixture import ALL_SHARD_DATA, ANIMAL_CLAIM, HUMAN_CLAIM, CatalogueTestCase, claim

from validate import main


class Control(CatalogueTestCase):
    def test_fixture_is_valid(self):
        """The fixture must pass cleanly, or every negative test below proves nothing.

        A test that asserts "rule N fires" passes just as happily when rule N fires
        on something the fixture got wrong.
        """
        report = self.assert_no_errors()
        self.assertEqual(
            [], report.warnings, "the fixture should also be warning-clean so warnings stay legible"
        )


class ParseErrors(CatalogueTestCase):
    """A file the loader cannot read as its documented shape must block the build.

    The trap these guard against is the truncated-or-mangled file that still parses
    as JSON: coerced silently to an empty catalogue, it once made the validator print
    "all rules pass" over a destroyed roster and let the build publish an empty
    catalogue from it.
    """

    def test_roster_with_wrong_top_level_type_blocks(self):
        self.write("roster.json", ["not", "an", "object"])
        self.assert_error("parse", "roster.json")

    def test_vocabulary_with_wrong_top_level_type_blocks(self):
        self.write("vocabulary/outcomes.json", "outcomes")
        self.assert_error("parse", "outcomes.json")

    def test_triage_with_wrong_top_level_type_blocks(self):
        """Silently treating this as 'no triage file' would erase every depth budget
        and re-commission triage for the whole roster."""
        self.write("triage.json", [])
        self.assert_error("parse", "triage.json")

    def test_wrong_typed_template_is_not_reported_as_missing(self):
        """'Missing' and 'unreadable' need opposite fixes: create it versus repair it."""
        self.write("templates/shard.json", ["skeleton"])
        report = self.validate()
        self.assertTrue(any(f.rule == "parse" and "templates" in f.where for f in report.errors))
        self.assertFalse(
            [w for w in report.warnings if "missing" in w.message and "templates" in w.where],
            "a template that exists but cannot be read should not also be called missing",
        )

    def test_a_shard_misfiled_directly_under_strains_is_reported(self):
        """A shard outside an entity directory belongs to no entity, so it would
        otherwise cease to exist - while coverage keeps reporting its pass as not run."""
        self.write("strains/orphan.json", dict(ALL_SHARD_DATA))
        self.assert_error("parse", "orphan.json")

    def test_a_stray_file_in_an_entity_directory_is_reported(self):
        """gi.json.bak is invisible to the loader, so an editor backup silently
        holding the only copy of a pass reads as the pass never having run."""
        with open(self.path("strains/test-strain/all.json.bak"), "w", encoding="utf-8") as fh:
            fh.write("{}")
        self.assert_error("parse", "all.json.bak")

    def test_hidden_files_are_ignored(self):
        """Lock files and .DS_Store are environment noise, not misfiled data."""
        with open(self.path("strains/test-strain/.all.json.lock"), "w", encoding="utf-8") as fh:
            fh.write("")
        self.assert_no_errors()


class ShardShape(CatalogueTestCase):
    """Structure the claim rules stand on. A malformed shard used to be silently
    filtered to an empty one, so a corrupted claim vanished from validation, the
    claim count, and the build with no finding anywhere."""

    def test_missing_claims_array(self):
        """A pass that found nothing writes claims: [] - that is a finding. A shard
        with no claims key at all does not say whether the pass found nothing or the
        writer forgot, and the two must not be conflated."""
        self.edit("strains/test-strain/all.json", lambda d: d.pop("claims"))
        self.assert_error("shape", "claims")

    def test_claims_not_a_list(self):
        """A non-iterable value, so this pins the isinstance check itself - a string
        here would also be caught downstream as per-character non-object entries."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"claims": 42}))
        self.assert_error("shape", "claims")

    def test_a_claim_that_is_not_an_object_is_reported_not_dropped(self):
        """The row exists in the file; a validator that cannot read it must say so
        rather than validate the shard as if it were absent."""
        self.edit("strains/test-strain/all.json", lambda d: d["claims"].append("not a claim"))
        self.assert_error("shape", "claims[3]")

    def test_body_systems_not_a_list(self):
        """Previously reported as 'no body_systems', which describes a different
        defect with a different fix."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"body_systems": "GI"}))
        self.assert_error("shape", "body_systems")

    def test_duplicate_body_system_declaration(self):
        """Seven entries spanning six systems is not a pass over all six; it is a
        declaration that cannot be trusted to mean either thing."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update({"body_systems": ["GI"] + d["body_systems"]}),
        )
        self.assert_rule(3)

    def test_pass_summary_not_a_string(self):
        self.edit("strains/test-strain/all.json", lambda d: d.update({"pass_summary": {"text": "x"}}))
        self.assert_error("shape", "pass_summary")

    def test_proposed_impacts_entry_not_an_object(self):
        self.edit("strains/test-strain/all.json", lambda d: d.update({"proposed_impacts": ["new outcome"]}))
        self.assert_error("shape", "proposed_impacts")


class SearchedEmptyShape(CatalogueTestCase):
    """searched_empty is the per-id coverage record: ids this pass individually
    searched and could not write a row for. Build and plan derive a deep pass's
    remaining debt from it (allowed minus claimed minus searched_empty), so a bad
    entry does more than misdescribe the pass - it hides real debt, or invents
    phantom debt that re-opens a finished pass."""

    def searched(self, value) -> None:
        self.edit("strains/test-strain/all.json", lambda d: d.update({"searched_empty": value}))

    def test_a_valid_record_is_not_a_finding(self):
        self.searched(["gi-ibs-global"])
        self.assert_no_errors()

    def test_must_be_a_list(self):
        self.searched("gi-ibs-global")
        self.assert_error("shape", "searched_empty")

    def test_entries_must_be_strings(self):
        self.searched(["gi-ibs-global", 3])
        self.assert_error("shape", "searched_empty")

    def test_an_unknown_id_records_a_search_of_nothing(self):
        """It subtracts nothing from any allowed set, so the debt arithmetic would
        silently ignore it and the search it records evaporates."""
        self.searched(["gi-mystery"])
        self.assert_error("shape", "gi-mystery")

    def test_an_excluded_outcome_was_never_owed(self):
        """Searching one is fine; recording it claims coverage of a question the
        vocabulary settled the other way."""
        self.searched(["skin-acne"])
        self.assert_error("shape", "skin-acne")

    def test_an_id_outside_the_shards_systems(self):
        """A GI pass recording an Immune search claims coverage that the immune
        pass's own debt arithmetic will never see."""
        self.write(
            "strains/test-strain/gi.json",
            {
                "strain_id": "test-strain",
                "body_systems": ["GI"],
                "last_reviewed": "2026-08-01",
                "pass_summary": "GI-only pass.",
                "claims": [],
                "proposed_impacts": [],
                "searched_empty": ["imm-urti-incidence"],
                "gaps": "",
            },
        )
        self.assert_error("shape", "imm-urti-incidence")

    def test_an_id_also_claimed_is_a_contradiction(self):
        """"Searched and could not write a row" next to that id's row: one of the
        two statements is false, and the file does not say which."""
        self.searched(["gi-aad-prevention"])
        self.assert_error("shape", "gi-aad-prevention")

    def test_a_repeated_id_is_an_error(self):
        self.searched(["gi-ibs-global", "gi-ibs-global"])
        self.assert_error("shape", "more than once")


class ClaimShape(CatalogueTestCase):
    """Field types within a claim. Two of these used to crash the validator with a
    raw TypeError - a traceback where a finding belongs - and the rest rendered
    garbage or broke the compiled markdown downstream."""

    def test_impact_id_not_a_string_is_a_finding_not_a_crash(self):
        """A JSON array here made rule 1's dedup key unhashable and took the whole
        validator down, and build.py with it."""
        self.edit_claim(0, impact_id=["gi-aad-prevention"])
        self.assert_error("shape", "impact_id")

    def test_population_not_a_string_is_a_finding_not_a_crash(self):
        self.edit_claim(0, population={"kind": "humans"})
        self.assert_error("shape", "population")

    def test_study_type_with_a_non_string_entry_is_a_finding_not_a_crash(self):
        """An object in the list crashed the rank lookup."""
        self.edit_claim(0, study_type=[{"type": "human_meta"}])
        self.assert_rule(5)

    def test_sources_as_a_string_not_a_list(self):
        """"; ".join over a bare string emits it character-joined - 'P; M; I; D; ...'
        in the CSV and the readable view, from data that validated cleanly."""
        self.edit_claim(0, sources="PMID:11111111")
        self.assert_error("shape", "sources")

    def test_a_non_string_source_entry(self):
        self.edit_claim(0, sources=[11111111])
        self.assert_error("shape", "sources")

    def test_free_text_must_be_a_string(self):
        """The renderer joins these into lines; a non-string would crash it, and the
        build runs only on validated data, so the check belongs here."""
        self.edit_claim(0, dose=42)
        self.assert_error("shape", "dose")

    def test_free_text_must_be_single_line(self):
        """Every free-text field lands in a markdown list item or a CSV cell. A
        newline escapes the list item, so the second line renders outside the row it
        belongs to - structure broken by fully 'valid' data."""
        self.edit_claim(0, tier_rationale="Line one.\nLine two.")
        self.assert_error("shape", "tier_rationale")

    def test_pass_summary_must_be_single_line(self):
        """It is rendered inside a blockquote; the second line would escape it."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d.update({"pass_summary": "First.\nSecond."}),
        )
        self.assert_error("shape", "pass_summary")


class RosterShape(CatalogueTestCase):
    """Same guarantee for the roster: an entity the validator cannot read must be
    reported, not silently dropped from the entity list (which is what happened -
    rule 8's 'every roster decision is auditable' was defeated by a non-object)."""

    def test_no_entities_array(self):
        self.write("roster.json", {"_version": "test", "excluded_entities": []})
        self.assert_error("shape", "entities")

    def test_entities_not_a_list(self):
        self.edit("roster.json", lambda d: d.update({"entities": "oops"}))
        self.assert_error("shape", "entities")

    def test_an_entity_that_is_not_an_object(self):
        self.edit("roster.json", lambda d: d["entities"].append("garbage-entry"))
        self.assert_error("shape", "entities")

    def test_an_exclusion_that_is_not_an_object(self):
        self.edit("roster.json", lambda d: d["excluded_entities"].append("garbage-exclusion"))
        self.assert_error("shape", "excluded_entities")

    def test_also_known_as_as_a_string(self):
        """A bare string joins character-by-character: 'Also known as: L, a, c, t...'
        in the readable view and the plan output."""
        self.edit_entity("test-strain", also_known_as="Lactobacillus rhamnosus TS-1")
        self.assert_error("shape", "also_known_as")

    def test_component_strains_as_a_string(self):
        self.edit_entity("product-test", component_strains="Lacticaseibacillus rhamnosus TS-1")
        self.assert_error("shape", "component_strains")

    def test_identity_field_not_a_string(self):
        self.edit_entity("test-strain", genus=42)
        self.assert_error("shape", "genus")


class Rule1Uniqueness(CatalogueTestCase):
    def test_duplicate_pair_in_one_shard(self):
        """(impact_id, population) is what makes "deduplicated" checkable rather than
        a judgment call each research pass makes differently. Two rows for one finding
        double-count it in every view built from the table."""

        def mutate(data):
            data["claims"].append(claim())

        self.edit("strains/test-strain/all.json", mutate)
        self.assert_rule(1)

    def test_same_pair_in_two_shards_of_one_entity(self):
        """Rule 1's scope is the directory, not the file.

        Sharding is what makes this reachable: two passes writing one entity can
        each hold a row the other cannot see. Placement (rule 11) is meant to make
        it impossible, so this case should fire both rules - rule 1 is the backstop
        that catches a collision rule 11 somehow let through.
        """
        gi_only = {
            **ALL_SHARD_DATA,
            "body_systems": ["GI"],
            "claims": [claim()],
        }
        immune_only = {
            **ALL_SHARD_DATA,
            "body_systems": ["Immune"],
            "claims": [claim()],
        }
        import os

        os.remove(self.path("strains/test-strain/all.json"))
        self.write("strains/test-strain/gi.json", gi_only)
        self.write("strains/test-strain/immune.json", immune_only)
        self.assert_rule(1)
        self.assert_rule(11, "a GI claim filed in the Immune shard")

    def test_same_impact_different_population_is_allowed(self):
        """Human and preclinical evidence are separate ladders, so one impact may
        legitimately carry a humans row and an animals row. If uniqueness were keyed
        on impact_id alone, recording mouse data would delete the human finding."""

        def mutate(data):
            data["claims"].append(
                {
                    **HUMAN_CLAIM,
                    "population": "animals",
                    "population_detail": "BALB/c mice",
                    "study_type": ["animal"],
                    "evidence_tier": "P",
                    "bias_assessment": "not_assessed",
                }
            )

        self.edit("strains/test-strain/all.json", mutate)
        self.assert_no_errors()


class Rule2Vocabulary(CatalogueTestCase):
    def test_unknown_impact_id(self):
        """A minted id defeats deduplication entirely: "improves IBS-SSS" and
        "reduces IBS symptoms" become two findings, and neither joins to a label."""
        self.edit_claim(0, impact_id="gi-invented-outcome")
        self.assert_rule(2)

    def test_excluded_outcome_used_as_impact_id(self):
        """Excluded outcomes are out of scope by decision, not by oversight. Silently
        accepting one would reopen a scope question that was already settled, and it
        would do so in a shard rather than in the vocabulary where it was decided."""
        self.edit_claim(0, impact_id="skin-acne")
        errors = self.assert_rule(2)
        self.assertTrue(
            any("excluded outcome" in e.message for e in errors),
            "the message must distinguish an excluded outcome from an unknown one - "
            "they need opposite fixes",
        )

    def test_label_stored_on_a_claim(self):
        """The vocabulary is the only home for a label. A copy on the row can disagree
        with it, and then one outcome renders under two names with no way to tell which
        is current."""
        self.edit_claim(0, health_impact="reduces antibiotic-associated diarrhea")
        self.assert_rule(2)


class Rule3Placement(CatalogueTestCase):
    def test_directory_not_on_roster(self):
        """Research attached to an entity nobody put on the roster has no provenance,
        no identity to join, and no sweep that can account for it."""
        self.write("strains/ghost-strain/all.json", {**ALL_SHARD_DATA, "strain_id": "ghost-strain"})
        self.assert_rule(3)

    def test_a_dropped_entity_with_leftover_shards_gets_the_sharper_hint(self):
        """"not a strain_id" sends someone hunting for a typo; the real fix is removing
        the research of an entity that was deliberately dropped."""
        self.write(
            "strains/product-excluded/all.json",
            {**ALL_SHARD_DATA, "strain_id": "product-excluded"},
        )
        matched = self.assert_rule(3)
        self.assertTrue(
            any("excluded_entities" in f.message for f in matched),
            "\n".join(str(f) for f in matched),
        )

    def test_shard_strain_id_disagrees_with_directory(self):
        """This is the copy-paste failure: a shard cloned from another entity keeps its
        strain_id and its claims then join to the wrong organism's identity."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"strain_id": "product-test"}))
        self.assert_rule(3)

    def test_filename_does_not_match_body_systems(self):
        """The filename is a claim about coverage. all.json means one pass covered all
        six systems; if it really covered GI only, coverage.md reports the entity as
        finished when five systems were never searched."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"body_systems": ["GI"]}))
        self.assert_rule(3)

    def test_partial_multi_system_shard_has_no_filename(self):
        """A pass covers one system or all six. Anything between has no filename, and
        guessing one would silently invent a coverage claim nobody made."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"body_systems": ["GI", "Immune"]}))
        self.assert_rule(3)

    def test_identity_copied_into_shard(self):
        """Identity lives in roster.json alone. A deep entity has several shards, so a
        copied field is several copies, and a taxonomy correction has to find them all."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"genus": "Lacticaseibacillus"}))
        self.assert_rule(3)


class Rule4StudyTypePopulation(CatalogueTestCase):
    def test_human_row_carrying_animal_evidence(self):
        """Preclinical evidence never feeds a human tier. A human row that lists animal
        studies has already merged the two ladders, whatever its tier says."""
        self.edit_claim(0, study_type=["human_meta", "animal"])
        self.assert_rule(4)

    def test_animal_row_with_extra_study_types(self):
        """An animals row is exactly ["animal"]: there is no such thing as an RCT in
        mice for this catalogue's purposes, and allowing the mix would let a preclinical
        row inherit a clinical grading unit."""
        self.edit_claim(1, study_type=["human_rct", "animal"])
        self.assert_rule(4)

    def test_in_vitro_row_with_other_study_types(self):
        """The in_vitro branch mirrors the animals one. Untested, it was the one branch
        of rule 4 free to rot without any test noticing."""
        self.edit(
            "strains/test-strain/all.json",
            lambda d: d["claims"].append(
                claim(
                    ANIMAL_CLAIM,
                    population="in_vitro",
                    population_detail="Caco-2 monolayers",
                    study_type=["animal"],
                )
            ),
        )
        self.assert_rule(4)

    def test_unrecognised_population(self):
        """A typo in population matches none of rule 4's branches, so without a domain
        check it would silently switch off rules 4 and 7 for that row - the validator
        would report success on a row it never checked."""
        self.edit_claim(0, population="human")
        self.assert_rule(4)


class Rule5StudyTypeOrder(CatalogueTestCase):
    def test_out_of_canonical_order(self):
        """study_type[0] is the grading unit only because the order is fixed. Reversed,
        the row claims to have been graded from its weakest evidence."""
        self.edit_claim(0, study_type=["human_rct", "human_meta"])
        self.assert_rule(5)

    def test_empty_study_type(self):
        """An empty list has no grading unit at all, so effect_size and the tier
        describe nothing. It passes rule 4 vacuously, which is exactly why rule 5 has
        to reject it."""
        self.edit_claim(0, study_type=[], evidence_tier="C", bias_assessment="not_assessed")
        self.assert_rule(5)

    def test_repeated_study_type(self):
        """A repeat sorts as ordered but means the row lists one evidence class twice,
        which reads as more independent evidence than exists."""
        self.edit_claim(0, study_type=["human_meta", "human_meta"])
        self.assert_rule(5)

    def test_unknown_study_type(self):
        """An unrecognised value has no rank, so it cannot be ordered and cannot be the
        grading unit."""
        self.edit_claim(0, study_type=["systematic_review"])
        self.assert_rule(5)


class Rule6TierA(CatalogueTestCase):
    def test_tier_a_without_a_meta_analysis(self):
        """Tier A means risk of bias was formally appraised by someone. Grading from
        abstracts cannot do that, so tier A without an SR is a claim the source policy
        cannot support."""
        self.edit_claim(0, study_type=["human_rct"])
        self.assert_rule(6)

    def test_tier_a_with_meta_but_bias_not_assessed(self):
        """Both halves are required. An SR that did not appraise bias gives a pooled
        number without the appraisal that is the whole reason tier A outranks tier B."""
        self.edit_claim(0, bias_assessment="not_assessed")
        self.assert_rule(6)

    def test_pooled_review_graded_from_its_own_trials_caps_at_b(self):
        """Tier rule 6's middle case, the most error-prone row in the catalogue: the SR
        pooled across a genus, so its estimate is not this strain's finding, but its
        included-studies table identifies this strain's trials with bias ratings.

        The row keeps bias_assessment sr_assessed - bias really was appraised - and
        rule 6 caps it at B because human_meta is absent. This must validate; if it
        did not, the honest encoding would be impossible and passes would be pushed
        toward claiming the pooled estimate instead.
        """
        self.edit_claim(
            0,
            study_type=["human_rct"],
            evidence_tier="B",
            bias_assessment="sr_assessed",
            tier_rationale="Only SR pools across the genus; graded from 3 strain-specific trials.",
        )
        self.assert_no_errors()


class Rule7PreclinicalTier(CatalogueTestCase):
    def test_animal_row_not_tier_p(self):
        """Tier P is what keeps the preclinical ladder separate. An animals row graded B
        makes mouse data look like clinical evidence in every sort of the table."""
        self.edit_claim(1, evidence_tier="B")
        self.assert_rule(7)

    def test_human_row_tier_p(self):
        """The rule is an iff in both directions: a human row hidden at tier P would be
        filtered out by anyone excluding preclinical evidence."""
        self.edit_claim(2, evidence_tier="P")
        self.assert_rule(7)

    def test_unrecognised_tier(self):
        """An unknown tier disables both tier rules for the row rather than failing."""
        self.edit_claim(0, evidence_tier="A+")
        self.assert_rule(7)


class Rule8Provenance(CatalogueTestCase):
    def test_entity_without_a_roster_source(self):
        """roster_source is what turns "is the roster complete?" into "was every source
        swept?". An entity without one cannot be audited or diffed against a re-run."""
        self.edit_entity("test-strain", roster_source="")
        self.assert_rule(8)

    def test_exclusion_without_a_strain_id(self):
        """An exclusion recorded only as free text cannot be matched against the sweep
        that re-proposes it, so the decision gets argued a second time."""

        def mutate(data):
            data["excluded_entities"][0].pop("strain_id")

        self.edit("roster.json", mutate)
        self.assert_rule(8)

    def test_id_in_both_lists(self):
        """An entity that is simultaneously on and off the roster makes every count
        wrong and leaves "was it dropped?" unanswerable."""

        def mutate(data):
            data["excluded_entities"].append(
                {"strain_id": "test-strain", "label": "Test", "reason": "dropped"}
            )

        self.edit("roster.json", mutate)
        self.assert_rule(8)

    def test_duplicate_strain_id_in_entities(self):
        """strain_id is the primary key for both joins. A duplicate makes the second
        entry unreachable, so its identity silently never appears while its claims do."""

        def mutate(data):
            data["entities"].append(dict(data["entities"][0]))

        self.edit("roster.json", mutate)
        self.assert_rule(8)

    def test_an_entity_without_a_strain_id(self):
        """No primary key means no join, no shard directory, and no way to triage it -
        the entity exists in the file and nowhere else."""
        self.edit("roster.json", lambda d: d["entities"][1].pop("strain_id"))
        self.assert_rule(8)

    def test_duplicate_strain_id_in_exclusions(self):
        """Same key, same failure on the other list: the second exclusion's reason is
        unreachable, so the record of why it was dropped depends on file order."""

        def mutate(data):
            data["excluded_entities"].append(dict(data["excluded_entities"][0]))

        self.edit("roster.json", mutate)
        self.assert_rule(8)


class Rule9EntityType(CatalogueTestCase):
    def test_product_without_components(self):
        """Catches a product entry whose composition was dropped. Without the iff it
        would read as a single strain and tier rule 2's ban on decomposing it would
        have nothing to bite on."""
        self.edit_entity("product-test", component_strains=[])
        self.assert_rule(9)

    def test_undisclosed_composition_is_a_statement_not_an_absence(self):
        """The guard rule for trade-secret products: an undisclosed designation is
        recorded as text, so the iff still holds. If it were recorded as an empty list,
        "nobody wrote it down" and "the manufacturer withholds it" would look identical.
        """
        self.edit_entity(
            "product-test",
            component_strains=["Saccharomyces cerevisiae (proprietary strain, designation not disclosed)"],
        )
        self.assert_no_errors()

    def test_single_strain_with_components(self):
        """A single_strain carrying components is a product that was typed wrong, and
        tier rule 2 would then permit its evidence to be attributed to one organism."""
        self.edit_entity("test-strain", component_strains=["Something else"])
        self.assert_rule(9)

    def test_unknown_entity_type(self):
        """The three types decide what evidence may attach to the entity. A fourth,
        invented one has no rule governing it."""
        self.edit_entity("test-strain", entity_type="unknown_single_strain_product")
        self.assert_rule(9)


class Rule10Preparation(CatalogueTestCase):
    def test_missing_preparation(self):
        """Live and heat-killed preparations of one strain are different products with
        different trials. Leaving it unstated hides that distinction behind a label that
        rarely makes it obvious."""
        self.edit_entity("test-strain", preparation=None)
        self.assert_rule(10)

    def test_unknown_preparation(self):
        self.edit_entity("test-strain", preparation="heat-killed")
        self.assert_rule(10)


class Rule11ShardPlacement(CatalogueTestCase):
    def test_claim_outside_its_shard_body_system(self):
        """This is what makes a cross-shard duplicate impossible rather than merely
        detectable. If a GI pass could file a mechanistic finding, the mechanistic pass
        would find the same paper and write it again in its own shard."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"body_systems": ["GI"]}))
        self.write(
            "strains/test-strain/gi.json", {**self.read("strains/test-strain/all.json")}
        )
        import os

        os.remove(self.path("strains/test-strain/all.json"))
        self.assert_rule(11, "mech-gut-barrier and safety-bacteremia in a GI-only shard")


class Rule12Counts(CatalogueTestCase):
    def test_zero_study_count(self):
        """0 is the template placeholder's shape and is type-valid, which is exactly why
        it leaks into real rows. It reads as a measured zero; null reads as unknown."""
        self.edit_claim(0, n_studies=0)
        self.assert_rule(12)

    def test_negative_participants(self):
        self.edit_claim(0, n_participants=-5)
        self.assert_rule(12)

    def test_null_is_allowed(self):
        """Case reports have no denominator. Forcing a number there would invent one."""
        self.edit_claim(0, n_participants=None)
        self.assert_no_errors()

    def test_boolean_is_not_a_count(self):
        """True is an int in Python and would pass a naive positivity check."""
        self.edit_claim(0, n_studies=True)
        self.assert_rule(12)


class Rule13EvidenceFields(CatalogueTestCase):
    def test_misspelled_direction(self):
        """`benefits` for `benefit` validates as a string and then drops out of every
        filter on direction: present in the data, absent from every view built on it.
        That is worse than a row nobody wrote, because nothing reports it missing."""
        self.edit_claim(0, direction="benefits")
        self.assert_rule(13)

    def test_missing_direction(self):
        """The row asserts nothing at all without it. `benefit`, `no effect` and `harm`
        are the whole point of the catalogue carrying nulls and harms alongside wins."""
        self.edit_claim(0, direction=None)
        self.assert_rule(13)

    def test_missing_industry_funding(self):
        """Absence is not the honest answer when `unclear` exists. Manufacturer
        sponsorship is unusually prevalent here and correlates with positive findings,
        so an empty field reads as "no concern" when it means "nobody looked"."""
        self.edit_claim(0, industry_funded=None)
        self.assert_rule(13)

    def test_unclear_is_a_real_answer(self):
        """The source policy expects `unclear` often - abstracts rarely carry funding.
        It must validate, or passes get pushed into guessing to satisfy rule 13."""
        self.edit_claim(0, industry_funded="unclear", independently_replicated="unclear")
        self.assert_no_errors()

    def test_misspelled_consistency(self):
        self.edit_claim(0, consistency="inconsistent")
        self.assert_rule(13)

    def test_misspelled_replication(self):
        self.edit_claim(0, independently_replicated="true")
        self.assert_rule(13)


class Rule14ReviewDate(CatalogueTestCase):
    def test_placeholder_date(self):
        """An unreplaced YYYY-MM-DD sorts *after* every real ISO date, so the oldest-pass
        rule would skip it and report the entity as fresher than its stalest pass - the
        staleness signal inverted rather than merely missing."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"last_reviewed": "YYYY-MM-DD"}))
        self.assert_rule(14)

    def test_missing_date(self):
        self.edit("strains/test-strain/all.json", lambda d: d.pop("last_reviewed"))
        self.assert_rule(14)

    def test_non_iso_ordering_is_rejected(self):
        """A US-order date is readable but sorts wrongly, which is the same defect in a
        shape that looks fine to a human reviewer."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"last_reviewed": "08/01/2026"}))
        self.assert_rule(14)

    def test_an_impossible_calendar_date_is_rejected(self):
        """2026-13-99 has the right shape and sorts *after* every real date, so it
        would never become the entity's oldest pass - the same freshness inversion
        the placeholder causes, wearing a digit costume."""
        self.edit("strains/test-strain/all.json", lambda d: d.update({"last_reviewed": "2026-13-99"}))
        self.assert_rule(14)

    def test_the_template_is_exempt(self):
        """templates/shard.json keeps its loud placeholder on purpose: it is a skeleton
        rather than a pass, and a real-looking date there would be copied verbatim into
        every shard written from it - the exact defect rule 14 exists to prevent."""
        self.assertEqual("YYYY-MM-DD", self.read("templates/shard.json")["last_reviewed"])
        self.assert_no_errors()


class Rule15TriageResolves(CatalogueTestCase):
    def test_entry_for_an_entity_that_does_not_exist(self):
        """Triage output commissions research. An entry naming nothing on the roster
        budgets passes for an entity nobody can research or identify."""

        def mutate(data):
            data["triage"].append(
                {**data["triage"][0], "strain_id": "invented-strain"}
            )

        self.edit("triage.json", mutate)
        self.assert_rule(15)

    def test_duplicate_triage_entry(self):
        """Two verdicts for one entity make the pass plan depend on which the reader
        reaches first, so the same entity gets a different depth budget by accident."""

        def mutate(data):
            data["triage"].append(dict(data["triage"][0]))

        self.edit("triage.json", mutate)
        self.assert_rule(15)

    def test_entry_without_a_strain_id(self):
        self.edit("triage.json", lambda d: d["triage"][0].pop("strain_id"))
        self.assert_rule(15)

    def test_a_dropped_entity_resolves_against_the_exclusion_list(self):
        """The triage record of a dropped entity is kept deliberately - it is the
        evidence the drop was confirmed rather than inferred. Rule 15 must accept it,
        or the audit trail would have to be deleted to satisfy the validator."""

        def mutate(data):
            data["triage"].append(
                {
                    "strain_id": "product-excluded",
                    "depth": "drop",
                    "triage_notes": "Criterion 2 fails.",
                }
            )

        self.edit("triage.json", mutate)
        self.assert_no_errors()

    def test_no_triage_file_is_not_a_violation(self):
        """Before triage runs there is nothing to check, and that is the starting state
        of every catalogue."""
        import os

        os.remove(self.path("triage.json"))
        self.assert_no_errors()


class Rule16Vocabulary(CatalogueTestCase):
    """The vocabulary is the join table every claim resolves through. A defect here
    does not announce itself - it silently redefines rules 2 and 11 for every claim
    that joins through the damaged row, which is why these are errors and not the
    warnings they used to be."""

    def test_duplicate_outcome_id(self):
        """Dict-comprehension joins mean the *last* duplicate wins. A second
        gi-aad-prevention under Immune would flip the join and generate false rule 11
        errors against shards that were filed correctly."""
        self.edit(
            "vocabulary/outcomes.json",
            lambda d: d["outcomes"].append(
                {"id": "gi-aad-prevention", "label": "reduces AAD", "body_system": "Immune"}
            ),
        )
        self.assert_rule(16)

    def test_missing_label(self):
        """The label is what the join exists to fetch; without one the readable view
        renders an empty heading over the claim."""
        self.edit("vocabulary/outcomes.json", lambda d: d["outcomes"][0].pop("label"))
        self.assert_rule(16)

    def test_missing_body_system(self):
        """An outcome with no body system slips through rules 3 and 11 entirely - no
        shard owns it, every shard accepts it - and renders an empty ### heading."""
        self.edit("vocabulary/outcomes.json", lambda d: d["outcomes"][0].pop("body_system"))
        self.assert_rule(16)

    def test_out_of_scope_body_system(self):
        """Skin is excluded by decision. An in-scope outcome pointing there makes
        every use of the id an unfixable rule 11 error - no shard may declare Skin."""
        self.edit(
            "vocabulary/outcomes.json",
            lambda d: d["outcomes"][0].update({"body_system": "Skin"}),
        )
        self.assert_rule(16)

    def test_id_on_both_lists(self):
        """In scope and out of scope at once: rule 2 would accept and reject the same
        claim depending on which list the reader consulted."""
        self.edit(
            "vocabulary/outcomes.json",
            lambda d: d["excluded_outcomes"].append(dict(d["outcomes"][0])),
        )
        self.assert_rule(16)

    def test_outcome_without_an_id(self):
        self.edit("vocabulary/outcomes.json", lambda d: d["outcomes"][0].pop("id"))
        self.assert_rule(16)

    def test_excluded_outcome_without_an_id(self):
        """Rule 2 matches excluded outcomes by id to tell 'out of scope by decision'
        from 'invented'. An id-less exclusion can never match, so the decision it
        records is unreachable."""
        self.edit("vocabulary/outcomes.json", lambda d: d["excluded_outcomes"][0].pop("id"))
        self.assert_rule(16)

    def test_an_outcome_that_is_not_an_object(self):
        self.edit("vocabulary/outcomes.json", lambda d: d["outcomes"].append("new outcome"))
        self.assert_error("shape", "outcomes")


class WarningsAreNotRules(CatalogueTestCase):
    """The two classes are separate on purpose. The line is whether the defect is
    representable in a finished catalogue: a row whose tier nobody justified is thin
    research and a normal intermediate state, while a row whose direction is unreadable
    is broken data and belongs to rule 13."""

    def test_missing_population_detail_warns(self):
        """SCHEMA.md's words: a claim without this is unfalsifiable. It is still not an
        invariant, because the honest fix is research, not a schema edit."""
        self.edit_claim(0, population_detail="")
        self.assert_warns("population_detail")

    def test_last_reviewed_on_a_claim_is_an_unknown_field(self):
        """SCHEMA.md's Provenance table: 'Not a claim field - it lives on the shard.'
        A per-claim date would sit outside the oldest-pass freshness rule, silently
        asserting a review that nothing computes with."""
        self.edit_claim(0, last_reviewed="2020-01-01")
        self.assert_warns("last_reviewed")

    def test_triage_depth_warns_rather_than_failing(self):
        """triage.py refuses an unknown depth at the write boundary, so this can only
        arrive by hand-editing. It sends the entity back to `untriaged` - no budget can
        be stated for it - rather than corrupting a row, which puts it on the
        reporting side of the line."""

        def mutate(data):
            data["triage"][0]["depth"] = "thorough"

        self.edit("triage.json", mutate)
        self.assert_warns("depth")

    def test_triage_drop_still_on_roster_warns(self):
        """Triage deciding "drop" and the roster still listing the entity means the
        two-step move was started and not finished."""

        def mutate(data):
            data["triage"][0]["depth"] = "drop"

        self.edit("triage.json", mutate)
        self.assert_warns("still in roster entities")

    def test_triage_naming_an_excluded_body_system_warns(self):
        """outcome_areas drives which passes run. An out-of-scope system there would
        commission a pass that is required to record nothing."""

        def mutate(data):
            data["triage"][0]["outcome_areas"] = ["GI", "Skin"]

        self.edit("triage.json", mutate)
        self.assert_warns("not an in-scope body system")


class Cli(CatalogueTestCase):
    def run_main(self, *argv: str) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["--root", self.root, *argv])
        return code, buffer.getvalue()

    def test_a_clean_catalogue_exits_zero(self):
        code, out = self.run_main()
        self.assertEqual(0, code, out)
        self.assertIn("pass", out)

    def test_a_single_violation_reads_singular(self):
        self.edit_claim(0, impact_id="gi-invented")
        code, out = self.run_main()
        self.assertEqual(1, code)
        self.assertIn("1 violation,", out)

    def test_strict_turns_warnings_into_failure(self):
        """--strict exists for a pre-publish gate: the same catalogue must pass loose
        and fail strict, or the flag silently means nothing."""
        self.edit_claim(0, population_detail="")
        code, _ = self.run_main()
        self.assertEqual(0, code)
        code, out = self.run_main("--strict")
        self.assertEqual(1, code)
        self.assertIn("--strict", out)


class TemplateIsCheckedAsData(CatalogueTestCase):
    def test_broken_template_fails_validation(self):
        """The template is the first thing a research pass copies. A defect there is
        reproduced into every shard written from it, so it is validated as a shard -
        with only its filename and placeholder dates exempted."""
        self.edit("templates/shard.json", lambda d: d["claims"][0].update({"evidence_tier": "A", "study_type": ["human_rct"]}))
        self.assert_rule(6)

    def test_template_placeholders_do_not_warn(self):
        """Its dates and PMIDs are deliberately fake; warning about them would train
        everyone to ignore the warning list."""
        report = self.validate()
        self.assertFalse(
            [w for w in report.warnings if "templates/" in w.where],
            "the template should not generate warnings",
        )


if __name__ == "__main__":
    unittest.main()
