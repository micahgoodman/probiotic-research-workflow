"""Load, check and summarise the catalogue. RULES.md is the design; rule numbers below refer to it."""
import collections
import glob
import json
import os
import re
from dataclasses import dataclass, field

TIER_B_TRIALS = 2  # rule 7: placebo-controlled trials an entity needs for tier B

EXCLUDED_REASONS = {  # rule 3
    "not_an_intervention_study", "not_a_probiotic", "retracted", "not_human", "not_oral", "entity_not_named", "secondary_report", "no_listed_condition", "not_accessible",
}
NOT_COUNTED_REASONS = {  # rule 5
    "not_measured", "instrument_not_listed", "subscale_only", "subgroup_only",
    "result_not_accessible",
}
OUTCOMES = ("benefit", "no_difference", "harm")  # rule 6
# "found", because a trial that finds no difference has not shown that there is none
OUTCOME_WORDS = {"benefit": "benefit", "no_difference": "no difference found", "harm": "harm"}
DESIGNS = ("randomized_placebo", "randomized_other_control", "not_randomized", "single_group")  # rule 3
COMPARISONS = ("between_groups", "within_group", "not_stated")  # rule 6

EXCLUDED_KEYS = {"pmid", "status", "excluded_reason", "of_pmid"}
ELIGIBLE_KEYS = {"pmid", "status", "design", "registration", "n_randomized", "population", "arms"}
ARM_KEYS = {"entity_as_stated", "strain_codes", "brand", "other_actives", "preparation",
            "dose_as_stated", "weeks", "results"}
COUNTED_KEYS = {"condition", "result", "instrument", "comparison", "main_endpoint"}
NOT_COUNTED_KEYS = {"condition", "result", "reason", "instrument_as_stated"}
FOUND_KEYS = {"url", "product", "country", "checked", "names"}   # rule 8: a page was found
NONE_FOUND_KEYS = {"url", "checked", "searched"}                   # rule 8: nothing is for sale


@dataclass
class Catalogue:
    root: str
    conditions: dict           # condition id -> condition
    aliases: dict
    search: dict               # condition id -> [pmid]
    available: dict            # entity key -> one product page, or the record that none was found
    trials: dict               # file stem -> record
    load_errors: list = field(default_factory=list)


def root_dir():
    return os.environ.get("CATALOGUE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_json(path):
    with open(path) as f:
        return json.load(f)


def load(root=None):
    root = root or root_dir()
    read = lambda rel: read_json(os.path.join(root, rel))
    cat = Catalogue(root, {c["id"]: c for c in read("conditions.json")["conditions"]},
                    read("aliases.json")["aliases"], {}, read("available.json")["available"], {})
    for path in sorted(glob.glob(os.path.join(root, "search", "*.json"))):
        listing = read_json(path)
        cat.search.setdefault(listing["condition"], []).extend(listing["pmids"])
    for path in sorted(glob.glob(os.path.join(root, "trials", "*.json"))):
        name = os.path.basename(path)
        try:
            cat.trials[name[:-5]] = read_json(path)
        except ValueError as e:
            cat.load_errors.append(f"trials/{name}: not valid JSON ({e})")
    return cat


# ---------- rule 4: the entity ----------

def _norm(text):
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def entity_key(arm, aliases):
    canon = lambda s: aliases.get(s, s)
    names = arm["strain_codes"] or [arm["brand"]]
    parts = [canon(_norm(n)) for n in names + arm["other_actives"]]
    if arm["preparation"] == "heat_killed":
        parts.append("heatkilled")
    return canon("+".join(sorted(parts)))


# ---------- the checker ----------

def _counted(result):
    return result.get("result") in OUTCOMES


def _is_trial_result(trial, result):
    """Rule 7: only a comparison against a placebo group, in a randomized trial, feeds tiers B and C."""
    return trial["design"] == "randomized_placebo" and result["comparison"] == "between_groups"


def _check_result(where, r, conditions, design):
    if not isinstance(r, dict) or r.get("condition") not in conditions:
        return [f"{where}: condition must be one of {sorted(conditions)}"]
    where = f"{where} {r['condition']}"
    allowed = COUNTED_KEYS if _counted(r) else NOT_COUNTED_KEYS
    errs = [f"{where}: unknown field '{k}'" for k in sorted(set(r) - allowed)]
    if _counted(r):
        listed = [i["id"] for i in conditions[r["condition"]]["instruments"]]
        if r.get("instrument") not in listed:
            errs.append(f"{where}: instrument '{r.get('instrument')}' is not on the list for "
                        f"{r['condition']} {listed}")
        if r.get("comparison") not in COMPARISONS:
            errs.append(f"{where}: comparison must be one of {COMPARISONS}")
        elif design == "single_group" and r["comparison"] == "between_groups":
            errs.append(f"{where}: a single_group study has no second group, so comparison cannot be between_groups")
        if r.get("main_endpoint") not in ("yes", "no", "not_stated"):
            errs.append(f"{where}: main_endpoint must be yes, no or not_stated")
    elif r.get("result") == "not_counted":
        if r.get("reason") not in NOT_COUNTED_REASONS:
            errs.append(f"{where}: reason must be one of {sorted(NOT_COUNTED_REASONS)}")
        if (r.get("reason") == "instrument_not_listed") != bool(r.get("instrument_as_stated")):
            errs.append(f"{where}: instrument_as_stated is required for instrument_not_listed, and only then")
    else:
        errs.append(f"{where}: result must be one of {OUTCOMES} or not_counted")
    return errs


def _check_arm(where, a, cat, design):
    if not isinstance(a, dict):
        return [f"{where}: an arm must be an object"]
    errs = [f"{where}: unknown field '{k}'" for k in sorted(set(a) - ARM_KEYS)]
    errs += [f"{where}: missing field '{k}'" for k in sorted(ARM_KEYS - set(a))]
    if errs:
        return errs
    if not a["entity_as_stated"]:
        errs.append(f"{where}: entity_as_stated is empty")
    if not a["strain_codes"] and not a["brand"]:
        errs.append(f"{where}: needs strain_codes or a brand (or exclude the paper as entity_not_named)")
    # Two names for one strain would build a key like "mcc1274+mcc1274", which matches
    # nothing. The record is wrong, so say so rather than quietly building that key.
    canon = collections.Counter(cat.aliases.get(_norm(c), _norm(c)) for c in a["strain_codes"])
    errs += [f"{where}: strain '{c}' is named twice in one arm; two names for one strain"
             for c, times in sorted(canon.items()) if times > 1]
    if a["preparation"] not in ("live", "heat_killed"):
        errs.append(f"{where}: preparation must be live or heat_killed")
    if not a["results"]:
        errs.append(f"{where}: results is empty")
    for r in a["results"]:
        errs += _check_result(where, r, cat.conditions, design)
    return errs


def _check_eligible(where, t, cat):
    errs = [f"{where}: unknown field '{k}'" for k in sorted(set(t) - ELIGIBLE_KEYS)]
    errs += [f"{where}: missing field '{k}'" for k in sorted(ELIGIBLE_KEYS - set(t))]
    if errs:
        return errs
    if t["design"] not in DESIGNS:
        errs.append(f"{where}: design must be one of {DESIGNS}")
    n = t["n_randomized"]
    if n is not None and not (isinstance(n, int) and n > 0):
        errs.append(f"{where}: n_randomized must be a positive whole number, or null when unknown")
    if not t["population"]:
        errs.append(f"{where}: population is empty")
    if not t["arms"]:
        errs.append(f"{where}: arms is empty")
    for i, a in enumerate(t["arms"]):
        errs += _check_arm(f"{where} arm {i}", a, cat, t["design"])
    if errs:
        return errs
    # Two arms that mean the same entity are one arm. A not_counted result carries no
    # instrument, so the score check below cannot see them; only the key can.
    arms = collections.Counter(entity_key(a, cat.aliases) for a in t["arms"])
    errs += [f"{where}: entity '{k}' is an arm twice; two arms that differ only in the "
             f"vehicle or the coating are one arm, and one trial must not be counted twice"
             for k, times in sorted(arms.items()) if times > 1]
    if errs:
        return errs
    # Several listed scores for one condition are welcome: reported_scores() picks one.
    # The same score twice is a second dose arm, or a record that contradicts itself.
    seen = collections.Counter((entity_key(a, cat.aliases), r["instrument"])
                               for a in t["arms"] for r in a["results"] if _counted(r))
    errs += [f"{where}: entity '{k}' has a {i} result twice; one score has one result, "
             f"and for several doses record the highest dose only"
             for (k, i), times in seen.items() if times > 1]
    answered = {r["condition"] for a in t["arms"] for r in a["results"]}
    errs += [f"{where}: the {c} search found this paper, so it needs a {c} result (not_measured is an answer)"
             for c in sorted(cat.search) if t["pmid"] in cat.search[c] and c not in answered]
    return errs


def _check_available(cat, sound):
    """Rule 8. Every entity that gets a row says whether a reader can buy it.

    `sound` is the eligible records that passed every other check, so each arm here is
    well formed. An entity has a row when one of its arms holds a counted result.
    """
    rows = {}
    for stem, t in sound:
        for a in t["arms"]:
            if any(map(_counted, a["results"])):
                rows.setdefault(entity_key(a, cat.aliases), stem)
    errs = []
    for key, stem in sorted(rows.items()):
        where = f"available.json: entity '{key}' (trials/{stem}.json)"
        e = cat.available.get(key)
        if not isinstance(e, dict):
            errs.append(f"{where}: has a row but no entry; record the product page, or that none was found (rule 8)")
            continue
        found = e.get("url") is not None
        allowed = FOUND_KEYS if found else NONE_FOUND_KEYS
        if set(e) != allowed:
            errs.append(f"{where}: fields must be exactly {sorted(allowed)}; an entry carries no opinion")
            continue
        blank = [k for k in allowed if k != "url" and not (isinstance(e[k], str) and e[k].strip())]
        if blank:
            errs.append(f"{where}: {', '.join(blank)} must be text; a found page must copy the words that name the entity")
        if found and not str(e["url"]).startswith("http"):
            errs.append(f"{where}: url must be a web address")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("checked", ""))):
            errs.append(f"{where}: checked must be a date, YYYY-MM-DD")
    return errs


def validate(cat, only=None):
    """Check every record. `only` narrows the report to the named pmids, so one
    researcher can check their own files while the rest of the catalogue is unread."""
    errs = [e for e in cat.load_errors
            if only is None or e.split("/")[1].split(".")[0] in only]
    found = {p for pmids in cat.search.values() for p in pmids}
    if only is None:
        recorded = {t.get("pmid") for t in cat.trials.values() if isinstance(t, dict)}
        errs += [f"PMID {p}: no record in trials/, but a saved search found it"
                 for p in sorted(found - recorded)]
    sound = []  # eligible records with no error of their own, for the checks that read across records
    for stem, t in sorted(cat.trials.items()):
        if only is not None and stem not in only:
            continue
        where = f"trials/{stem}.json"
        if not isinstance(t, dict) or t.get("pmid") != stem:
            errs.append(f"{where}: the file name must be the record's pmid")
            continue
        if stem not in found:
            errs.append(f"{where}: PMID {stem} is not on any saved search list (rule 2)")
        if t.get("status") == "excluded":
            errs += [f"{where}: unknown field '{k}'" for k in sorted(set(t) - EXCLUDED_KEYS)]
            if t.get("excluded_reason") not in EXCLUDED_REASONS:
                errs.append(f"{where}: excluded_reason must be one of {sorted(EXCLUDED_REASONS)}")
            first = cat.trials.get(t.get("of_pmid"))
            if t.get("excluded_reason") == "secondary_report":
                # The first report is often a paper our six searches never found, so it has
                # no record of its own. We only check the pointer when we do hold that paper.
                if not t.get("of_pmid"):
                    errs.append(f"{where}: secondary_report needs of_pmid, the first report's pmid")
                # When the first report was itself excluded, this trial is counted no
                # times at all. Nobody can fix that, so it is counted in the screening
                # report rather than raised here as an error that would stop the build.
                # One excluded first report is different: a pointer at another
                # secondary_report hides the trial's own record, which is sitting right
                # there, and makes the screening report cry loss over nothing. Whoever
                # wrote this record can always fix it, so it is an error.
                elif first is not None and first.get("excluded_reason") == "secondary_report":
                    errs.append(
                        f"{where}: of_pmid {t['of_pmid']} is itself a secondary_report; "
                        f"point at the trial's own record, {first.get('of_pmid')}")
            elif "of_pmid" in t:
                errs.append(f"{where}: of_pmid is only for secondary_report")
        elif t.get("status") == "eligible":
            mine = _check_eligible(where, t, cat)
            errs += mine
            if not mine:
                sound.append((stem, t))
        else:
            errs.append(f"{where}: status must be eligible or excluded")
    errs += _check_available(cat, sound)
    return errs


# ---------- rule 7: tiers and verdicts ----------

@dataclass
class Tally:
    benefit: int = 0
    no_difference: int = 0
    harm: int = 0

    @property
    def total(self):
        return self.benefit + self.no_difference + self.harm

    def words(self, one, many):
        k = self.total
        if k == 1:
            outcome = "harm" if self.harm else "benefit" if self.benefit else "no_difference"
            return f"{OUTCOME_WORDS[outcome]} in the one {one}"
        if self.harm:
            return f"harm in {self.harm} of {k} {many}"
        if self.benefit == k:
            return f"benefit in all {k} {many}"
        if self.benefit == 0:
            return f"{OUTCOME_WORDS['no_difference']} in all {k} {many}"
        return f"mixed: benefit in {self.benefit} of {k} {many}"


@dataclass
class Verdict:
    condition: str
    entity: str
    label: str
    strong: Tally              # randomized, placebo group, compared between the groups
    weaker: Tally              # every other human result
    trial_pmids: list
    weaker_pmids: list
    # the fields below describe the studies the verdict rests on: the trials when there
    # is one, and the weaker studies only for tier D
    basis: list                # (pmid, result, n_randomized), in pmid order
    main_endpoint_trials: int
    people: int
    studies_without_size: int

    @property
    def trials(self):
        return self.strong.total

    @property
    def tier(self):
        return "B" if self.trials >= TIER_B_TRIALS else "C" if self.trials else "D"

    @property
    def verdict(self):
        if self.trials:
            return self.strong.words("trial", "trials")
        return self.weaker.words("weaker study", "weaker studies")


def reported_scores(cat):
    """Rule 5. Every listed score each trial reports, per entity and condition, best first.

    The record holds what the paper reports; this function is the only place that says
    which score speaks for the trial. It is the first one: the score nearest the top of
    the condition's list. Call only on a catalogue that passes validate().
    """
    rank = {c: [i["id"] for i in cond["instruments"]] for c, cond in cat.conditions.items()}
    found = collections.defaultdict(list)
    for t in cat.trials.values():
        for a in t.get("arms", []):
            for r in filter(_counted, a["results"]):
                found[(t["pmid"], entity_key(a, cat.aliases), r["condition"])].append((t, a, r))
    return {k: sorted(hits, key=lambda h: rank[k[2]].index(h[2]["instrument"]))
            for k, hits in found.items()}


def verdicts(cat):
    """One Verdict per entity and condition. Call only on a catalogue that passes validate()."""
    groups = collections.defaultdict(list)
    for (_, key, condition), hits in reported_scores(cat).items():
        groups[(condition, key)].append(hits[0])
    out = []
    for (condition, key), hits in groups.items():
        strong = [h for h in hits if _is_trial_result(h[0], h[2])]
        weak = [h for h in hits if not _is_trial_result(h[0], h[2])]
        basis = strong or weak
        tally = lambda group: Tally(**collections.Counter(r["result"] for _, _, r in group))
        names = collections.Counter(a["entity_as_stated"] for _, a, _ in hits)
        sizes = [t["n_randomized"] for t, _, _ in basis]
        out.append(Verdict(
            condition, key, min(names, key=lambda n: (-names[n], n)), tally(strong), tally(weak),
            sorted(t["pmid"] for t, _, _ in strong), sorted(t["pmid"] for t, _, _ in weak),
            sorted((t["pmid"], r["result"], t["n_randomized"]) for t, _, r in basis),
            sum(r["main_endpoint"] == "yes" for _, _, r in basis),
            sum(s for s in sizes if s), sizes.count(None)))
    order = list(cat.conditions)
    return sorted(out, key=lambda v: (order.index(v.condition), v.tier, -(v.trials or v.weaker.total), v.label))
