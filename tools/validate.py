"""Check records against RULES.md. Exit code 1 when anything is wrong.

    python3 tools/validate.py                 check the whole catalogue
    python3 tools/validate.py 123 456         check only those papers
"""
import sys

import catalogue as C


def main(argv):
    only = set(argv) or None
    cat = C.load()
    errs = C.validate(cat, only=only)
    for e in errs:
        print("ERROR", e)
    if only:
        print(f"checked {len(only)} papers; {len(errs)} errors")
    else:
        found = {p for pmids in cat.search.values() for p in pmids}
        print(f"{len(cat.trials)} records for {len(found)} papers found by the searches; "
              f"{len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
