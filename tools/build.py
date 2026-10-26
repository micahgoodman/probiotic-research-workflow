"""Check the records, then write build/catalogue.md, build/catalogue.csv and build/screening.md."""
import collections
import csv
import os
import re
import sys

import catalogue as C


TIERS = [("B", f"{C.TIER_B_TRIALS} or more randomized trials compared the probiotic with a placebo group"),
         ("C", "exactly one such trial"),
         ("D", "no such trial, only weaker studies: no placebo group, no random assignment, "
               "or a change inside one group with no comparison against placebo")]


def _people(v):
    if not v.people:
        return "unknown"
    unknown = f" (+{v.studies_without_size} of unknown size)" if v.studies_without_size else ""
    return f"{v.people}{unknown}"


def _each_study(v):
    return "; ".join(f"{C.OUTCOME_WORDS[result]} ({f'{n} people' if n else 'size unknown'})"
                     for _, result, n in v.basis)


def _weaker(v):
    if not v.trials or not v.weaker.total:
        return ""
    return f"{v.weaker.words('weaker study', 'weaker studies')} ({', '.join(v.weaker_pmids)})"


def _where_to_buy(e):
    return f"[{e['product']}]({e['url']}) ({e['country']}, checked {e['checked']})"


def _tables(cat, rows, buy):
    """One table per condition. On the buyable page each row also says where (rule 8)."""
    out = []
    for cid, cond in cat.conditions.items():
        mine = [v for v in rows if v.condition == cid]
        if not mine:
            continue
        out += [f"## {cond['label']}", "", f"Benefit means {cond['benefit_means']}.", ""]
        out += ["| Tier | Probiotic | " + ("Where to buy | " if buy else "") + "Verdict | Each study | "
                "People in total | Main endpoint in | Weaker studies also found | PubMed ids |",
                "|---|---|---|---|---|---|---|---|" + ("---|" if buy else "")]
        out += [f"| {v.tier} | {v.label} | " + (f"{_where_to_buy(cat.available[v.entity])} | " if buy else "")
                + f"{v.verdict} | {_each_study(v)} | {_people(v)} | {v.main_endpoint_trials} | {_weaker(v)} | "
                f"{', '.join(p for p, _, _ in v.basis)} |" for v in mine]
        out.append("")
    return out


def _catalogue_md(cat, rows):
    out = ["# Probiotic evidence catalogue", "",
           "The tier says how much evidence exists. It does not say how good the result was; the verdict "
           "does. A program computes both by counting studies. It does not weigh them, so read the "
           "number of people too. RULES.md explains every column.", ""]
    out += [f"- **Tier {t}**: {meaning}." for t, meaning in TIERS]
    out += ["- Tier A (a review that pools one strain's trials) and tier P (animal and lab studies) are not used.", ""]
    # Rule 8: the same rows, on two pages. The page is the only difference.
    buy = [v for v in rows if cat.available[v.entity]["url"] is not None]
    rest = [v for v in rows if cat.available[v.entity]["url"] is None]
    out += ["# Available to buy today", "",
            "Each row names one consumer product page that sells this probiotic, with the date it "
            "was checked. Pages change; nothing more is promised.", ""]
    out += _tables(cat, buy, True) or ["No entity with a row has a product page on record (see available.json).", ""]
    out += ["# Not yet available to buy", "",
            "The same rules and the same evidence, for probiotics nobody could find on sale.", ""]
    out += _tables(cat, rest, False) or ["None.", ""]
    return "\n".join(out)


def _names_listed(cat, condition, text):
    """The scores on this condition's list whose id or alias appears in `text`, as whole words.

    Only this condition's list: in the first run (18 October 2026) matching every list gave
    three permanent false marks (a depression scale's domains used for anxiety and sleep, and
    a cognition score whose abbreviation is also a depression score's) and no true one.
    """
    words = lambda x: " " + re.sub(r"[^a-z0-9]+", " ", x.lower()).strip() + " "
    hay = words(text)
    return sorted(i["id"] for i in cat.conditions[condition]["instruments"]
                  if any(words(n) in hay for n in [i["id"], *i["aliases"]]))


def _screening_md(cat):
    excluded = collections.Counter(t["excluded_reason"] for t in cat.trials.values() if t["status"] == "excluded")
    results = [r for t in cat.trials.values() for a in t.get("arms", []) for r in a["results"]]
    reasons = collections.Counter(r["reason"] for r in results if r["result"] == "not_counted")
    unlisted = collections.Counter((r["condition"], r["instrument_as_stated"]) for r in results
                                   if r.get("instrument_as_stated"))
    eligible = sum(t["status"] == "eligible" for t in cat.trials.values())
    out = ["# Screening report", "",
           f"{len(cat.trials)} papers have a record: {eligible} eligible and {sum(excluded.values())} excluded.",
           "", "## Excluded papers, by reason", ""]
    out += [f"- `{k}`: {n}" for k, n in excluded.most_common()] or ["- none"]
    out += ["", "## Results that do not count, by reason", ""]
    out += [f"- `{k}`: {n}" for k, n in reasons.most_common()] or ["- none"]
    lost = sorted((t["pmid"], t["of_pmid"]) for t in cat.trials.values()
                  if t.get("excluded_reason") == "secondary_report"
                  and cat.trials.get(t["of_pmid"], {}).get("status", "excluded") != "eligible")
    out += ["", "## Trials counted no times at all", "",
            "These papers report a trial whose first report is not in the catalogue, usually "
            "because that first paper is behind a paywall. The trial has no row of its own.", ""]
    out += [f"- {pmid} reports the trial first published as {of} ({len(lost)} in total)"
            for pmid, of in lost] or ["- none"]
    # Two papers under one registration number are one trial twice or two honest trials
    # from one registered programme; only a reader of both can tell, so the checker does
    # not refuse them (ruled 18 October 2026). They are listed here so somebody looks.
    shared = collections.defaultdict(list)
    for t in cat.trials.values():
        if t["status"] == "eligible" and t.get("registration"):
            shared[t["registration"]].append(t["pmid"])
    shared = sorted((reg, sorted(pmids)) for reg, pmids in shared.items() if len(pmids) > 1)
    out += ["", "## Registration numbers on more than one eligible record", "",
            "Each number below is on two or more eligible records. They are one trial reported "
            "twice (then the later paper is a secondary_report, rule 3) or two trials from one "
            "registered programme. Only a reader of both papers can tell which.", ""]
    out += [f"- {reg}: {', '.join(pmids)}" for reg, pmids in shared] or ["- none"]
    # User ruling, 21 September 2026: keep the naming rule and show what it costs.
    # An unnamed product cannot be looked up, so the catalogue refuses the paper. The
    # price is real evidence, and it is printed here paper by paper so it stays arguable.
    naming = {"not_accessible": "nobody could read the full text",
              "entity_not_named": "the paper names only a species, with no code or brand"}
    lost_names = sorted((t["pmid"], naming[t["excluded_reason"]]) for t in cat.trials.values()
                        if isinstance(t, dict) and t.get("excluded_reason") in naming)
    out += ["", "## Evidence lost because the product was not named", "",
            "These %d papers may hold real results. They are not in the catalogue because "
            "nobody can say which strain was tested, so no reader could act on them." % len(lost_names), ""]
    out += [f"- {pmid}: {why}" for pmid, why in lost_names] or ["- none"]
    # The ranking in rule 5 picks one score per trial. Where a trial's scores disagree,
    # that pick decides the result, so each such trial is named here with every score.
    split = sorted((pmid, c, hits) for (pmid, _, c), hits in C.reported_scores(cat).items()
                   if len({r["result"] for _, _, r in hits}) > 1)
    out += ["", "## Trials where the choice of score changes the result", "",
            "Each of these %d trials reports two or more listed scores that disagree. The "
            "score nearest the top of the list is used; the others are shown so the rule's "
            "cost stays visible." % len(split), ""]
    out += ["- %s %s: %s" % (pmid, c, "; ".join(
                f"{r['instrument']} {r['result']}" + (" (used)" if n == 0 else "")
                + (" [main endpoint]" if r["main_endpoint"] == "yes" else "")
                for n, (_, _, r) in enumerate(hits)))
            for pmid, c, hits in split] or ["- none"]
    # Rule 5: a note that names a score already on a list is a record to read again, not a
    # list to extend. Marking it here is what makes that re-read mechanical after each batch.
    out += ["", "## Scores that are not on a list", "",
            "A score that appears often here is a reason to extend a list in conditions.json. "
            "One marked [names a listed score] is a record to read again against that list.", ""]
    out += [f"- {c}: {name} ({n})" + (f" [names a listed score: {', '.join(hit)}]" if hit else "")
            for (c, name), n in unlisted.most_common() for hit in [_names_listed(cat, c, name)]] or ["- none"]
    return "\n".join(out) + "\n"


def _progress(cat):
    """How much of the search has been read. Shown so nobody mistakes a part-done page
    for the finished catalogue."""
    found = {p for pmids in cat.search.values() for p in pmids}
    read = len(found & set(cat.trials))
    left = len(found) - read
    if not left:
        return "\nAll %d papers the searches found have been read.\n" % len(found)
    return ("\n**This catalogue is not finished.** %d of %d papers found by the searches "
            "have been read; %d are still to read.\n" % (read, len(found), left))


def build(root=None):
    cat = C.load(root)
    # A wrong record blocks the build. A paper nobody has read yet does not: between waves
    # of research we need to read the page to catch a bad rule early.
    errs = C.validate(cat, only=set(cat.trials))
    if errs:
        for e in errs:
            print("ERROR", e)
        print(f"{len(errs)} errors. Nothing was written.")
        return 1
    rows = C.verdicts(cat)
    out_dir = os.path.join(cat.root, "build")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "catalogue.md"), "w") as f:
        f.write(_catalogue_md(cat, rows) + _progress(cat))
    with open(os.path.join(out_dir, "screening.md"), "w") as f:
        f.write(_screening_md(cat))
    with open(os.path.join(out_dir, "catalogue.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition", "tier", "entity", "label", "available_url", "available_checked", "verdict", "each_study",
                    "trial_benefit", "trial_no_difference", "trial_harm", "weaker_benefit", "weaker_no_difference",
                    "weaker_harm", "main_endpoint_trials", "people", "studies_without_size", "trial_pmids", "weaker_pmids"])
        for v in rows:
            e = cat.available[v.entity]
            w.writerow([v.condition, v.tier, v.entity, v.label, e["url"] or "", e["checked"], v.verdict, _each_study(v),
                        v.strong.benefit, v.strong.no_difference, v.strong.harm, v.weaker.benefit, v.weaker.no_difference,
                        v.weaker.harm, v.main_endpoint_trials, v.people, v.studies_without_size,
                        " ".join(v.trial_pmids), " ".join(v.weaker_pmids)])
    print(_progress(cat).strip())
    tiers = collections.Counter(v.tier for v in rows)
    buyable = sum(cat.available[v.entity]["url"] is not None for v in rows)
    print(f"wrote build/ from {len(cat.trials)} records: " + ", ".join(f"{tiers[t]} tier {t}" for t, _ in TIERS)
          + f"; {buyable} of {len(rows)} rows are available to buy today")
    return 0


if __name__ == "__main__":
    sys.exit(build())
