"""Find two shapes of record error across the whole catalogue at once.

Rule 4 (one strain, one code) and rule 3 (a blend is named only when every strain in it
is named) were each broken by records that looked fine one at a time. This scan lists the
candidates so a person checks a short list instead of re-reading 338 eligible records.

(a) An arm lists a deposit number (DSM, CECT, ATCC...) beside another code. Usually one
    strain written under two names, which splits an entity (PMIDs 37571403, 37576702,
    33545934 were this). A deposit number that aliases.json already maps is skipped: it is
    a strain's known name, not a second name (DSM23233 is B. longum 04). An arm whose codes
    are all deposit numbers is not flagged either: two deposit numbers are two strains.
(b) An arm's `entity_as_stated` names more organisms than the arm has codes, and no brand.
    Usually a blend recorded under the one strain that had a code (PMIDs 40722352,
    42255712, 38172876 were this and are now `entity_not_named`).

Both are heuristics: every hit needs eyes. Run from the project root:

    python3 notes/scripts/shape-scan.py
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import catalogue as C  # noqa: E402

cat = C.load(ROOT)
avail = {k: e["url"] is not None for k, e in cat.available.items()}
dep = re.compile(r"^(DSM|DSMZ|ATCC|NCIMB|CNCM|LMG|KCTC|CECT|CCTCC|CGMCC|NRRL|BCRC|NBRC|JCM|CCUG|KCCM|CCM|PTA"
                 r"|NCFB|NCTC|IFO|CBS|MTCC|BNCC)\s*(?:PTA\s*)?[A-Z]?-?\s*\d", re.I)
genus = re.compile(r"\b(Lactobacillus|Lacticaseibacillus|Lactiplantibacillus|Limosilactobacillus|Ligilactobacillus"
                   r"|Levilactobacillus|Lactococcus|Bifidobacterium|Streptococcus|Saccharomyces|Bacillus|Enterococcus"
                   r"|Clostridium|Akkermansia|Pediococcus|Propionibacterium|Heyndrickxia|Weizmannia|Faecalibacterium"
                   r"|Escherichia|Leuconostoc|Weissella|Bacteroides|L\.|B\.|S\.|E\.|P\.|Lc\.|Lp\.)\s+[a-z]{3,}", re.I)
a_hits, b_hits = [], []
for stem, t in sorted(cat.trials.items()):
    if t.get("status") != "eligible":
        continue
    for a in t["arms"]:
        codes = a["strain_codes"]
        key = C.entity_key(a, cat.aliases)
        d = [c for c in codes if dep.match(c.strip()) and C._norm(c) not in cat.aliases]
        plain = [c for c in codes if not dep.match(c.strip())]
        if d and plain:
            a_hits.append((stem, codes, a["entity_as_stated"][:90], key, avail.get(key)))
        species = len({m.group(0).lower() for m in genus.finditer(a["entity_as_stated"])})
        if codes and species > len(codes) and not a["brand"]:
            b_hits.append((stem, codes, species, a["entity_as_stated"][:110], key, avail.get(key)))
print(len(a_hits), "arms list a deposit number beside another code:")
for h in a_hits:
    print(" ", h[0], h[1], "|", h[2], "| AVAILABLE" if h[4] else "")
print()
print(len(b_hits), "arms name more organisms than they have codes (heuristic, needs eyes):")
for h in b_hits:
    print(" ", h[0], h[1], "species~", h[2], "|", h[3], "| AVAILABLE" if h[5] else "")
