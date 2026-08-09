#!/usr/bin/env python3
"""Records triage verdicts, and performs the one roster mutation triage may make.

    python3 tools/triage.py record --file entries.json
    python3 tools/triage.py record --json '{"strain_id": "...", "depth": "deep", ...}'
    python3 tools/triage.py drop <strain_id> "<reason>"

Why a tool rather than editing triage.json directly:

  triage.json is one file that every triage pass appends to. Unlike a shard, it has
  no exclusive owner, so two passes that each read-modify-write it lose one set of
  entries with no error. `record` takes a lock, merges by strain_id, and replaces
  the file atomically.

  `drop` moves an entity to excluded_entities in one roster.json write, keeping its
  strain_id. Done by hand it is easy to delete the entity and write a free-text
  label, and then the next sweep re-proposes it with nothing to match against - the
  exact failure excluded_entities exists to prevent.

Both refuse to write anything they would then have to warn about. validate.py is
tolerant when reading because a half-finished catalogue is normal; these are strict
when writing because nothing here is ever a normal intermediate state.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from catalogue import (
    BODY_SYSTEMS,
    DEPTHS,
    TRIAGE_FIELDS,
    Catalogue,
    display_name,
    file_lock,
    load_json,
    write_json,
    resolve_root,
)

TRIAGE_HEADER = {
    "_comment": (
        "Per-entity literature volume and depth budget. Written by the triage stage, "
        "consumed by the research stage to decide how many passes an entity gets. "
        "Counts are estimates for budgeting only and are never a source for a claim's "
        "n_studies or n_participants. Entries for dropped entities are kept: they are "
        "the record that the drop was confirmed rather than inferred. "
        "Write through tools/triage.py, not by hand. See ../SCHEMA.md, section Triage."
    ),
    "_version": "1.0",
}

REQUIRED_UNLESS_DROP = [
    "n_systematic_reviews",
    "n_human_trials",
    "has_preclinical_only_areas",
    "outcome_areas",
]


class TriageError(Exception):
    """A refusal to write. The message names the fix."""


def _validate_entry(entry: dict, cat: Catalogue) -> dict:
    if not isinstance(entry, dict):
        raise TriageError(f"entry is not an object: {entry!r}")

    strain_id = entry.get("strain_id")
    if not strain_id:
        raise TriageError("entry has no strain_id")
    if strain_id not in cat.entity_by_id and strain_id not in cat.excluded_by_id:
        raise TriageError(
            f"{strain_id}: not a strain_id in roster.json. Triage records verdicts about "
            "roster entities; adding one is a sweep's job, not triage's."
        )

    unknown = sorted(k for k in entry if k not in TRIAGE_FIELDS and not k.startswith("_"))
    if unknown:
        raise TriageError(f"{strain_id}: unknown field(s) {unknown}; allowed: {TRIAGE_FIELDS}")

    depth = entry.get("depth")
    if depth not in DEPTHS:
        raise TriageError(f"{strain_id}: depth {depth!r} not in {DEPTHS}")

    # Triage that records no reasoning cannot be audited, and its depth call cannot be
    # revisited by anyone who did not make it.
    if not str(entry.get("triage_notes") or "").strip():
        raise TriageError(
            f"{strain_id}: triage_notes is required - what was searched, what was found, "
            "and for a drop, which inclusion criterion failed"
        )

    if depth != "drop":
        missing = [f for f in REQUIRED_UNLESS_DROP if entry.get(f) is None]
        if missing:
            raise TriageError(f"{strain_id}: missing {missing} (required unless depth is 'drop')")

    # A drop may omit the counts - they budget research that will not happen - but a
    # field that is present is validated the same at every depth. Present-and-wrong
    # is never a normal intermediate state.
    for field_name in ("n_systematic_reviews", "n_human_trials"):
        value = entry.get(field_name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TriageError(f"{strain_id}: {field_name} must be a non-negative integer, got {value!r}")

    preclinical = entry.get("has_preclinical_only_areas")
    if preclinical is not None and not isinstance(preclinical, bool):
        raise TriageError(f"{strain_id}: has_preclinical_only_areas must be true or false")

    areas = entry.get("outcome_areas")
    if areas is not None:
        if not isinstance(areas, list):
            raise TriageError(f"{strain_id}: outcome_areas must be a list")
        bad = [a for a in areas if a not in BODY_SYSTEMS]
        if bad:
            raise TriageError(
                f"{strain_id}: outcome_areas names {bad}, which is out of scope. Excluded "
                "systems are never recorded here; note them in triage_notes if they bear "
                "on the depth call."
            )
        repeated = sorted({a for a in areas if areas.count(a) > 1})
        if repeated:
            raise TriageError(f"{strain_id}: outcome_areas names {repeated} more than once")
        if not areas and depth != "drop":
            raise TriageError(
                f"{strain_id}: outcome_areas is empty but depth is {depth!r}. An entity with "
                "no in-scope evidence fails criterion 3 and belongs at depth 'drop'."
            )
    return dict(entry)


def _require_readable(cat: Catalogue) -> None:
    """Refuse to write against inputs that did not parse, naming the broken file.

    Without this, a corrupt roster.json reads as an empty roster and every entry is
    refused as "not a strain_id in roster.json", and a corrupt triage.json surfaces
    as a JSON error attributed to the caller's input - both send the operator to fix
    the wrong thing.
    """
    for rel, message in cat.parse_errors:
        if rel in ("roster.json", "triage.json"):
            raise TriageError(f"cannot read {rel}: {message}")


def record(root: str, entries: list[dict]) -> list[str]:
    """Upsert triage entries by strain_id. Validates everything before writing anything."""
    root = resolve_root(root)
    cat = Catalogue.load(root)
    _require_readable(cat)
    validated = [_validate_entry(entry, cat) for entry in entries]

    ids = [e["strain_id"] for e in validated]
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    if repeated:
        raise TriageError(
            f"batch names {repeated} more than once; the upsert would keep only the "
            "last verdict for each, with no error"
        )

    path = os.path.join(root, "triage.json")
    with file_lock(path):
        data = load_json(path) if os.path.exists(path) else {**TRIAGE_HEADER, "triage": []}
        existing = data.get("triage")
        if not isinstance(existing, list):
            raise TriageError("triage.json has no 'triage' array")
        by_id = {e.get("strain_id"): i for i, e in enumerate(existing) if isinstance(e, dict)}
        for entry in validated:
            index = by_id.get(entry["strain_id"])
            if index is None:
                by_id[entry["strain_id"]] = len(existing)
                existing.append(entry)
            else:
                existing[index] = entry
        write_json(path, data)
    return [e["strain_id"] for e in validated]


def drop(root: str, strain_id: str, reason: str) -> str:
    """Move a triaged-as-drop entity to excluded_entities, keeping its strain_id."""
    root = resolve_root(root)
    if not reason.strip():
        raise TriageError("a drop needs a reason; an exclusion nobody can read gets re-argued")

    path = os.path.join(root, "roster.json")
    with file_lock(path):
        cat = Catalogue.load(root)
        _require_readable(cat)

        if strain_id in cat.excluded_by_id:
            raise TriageError(f"{strain_id} is already in excluded_entities")
        entity = cat.entity_by_id.get(strain_id)
        if entity is None:
            raise TriageError(f"{strain_id} is not in roster entities")

        # "A drop is confirmed, never inferred from known_for." Requiring the triage
        # record first is what makes that the tool's behaviour rather than an
        # instruction someone has to remember.
        triage_entry = cat.triage_by_id.get(strain_id)
        if triage_entry is None or triage_entry.get("depth") != "drop":
            raise TriageError(
                f"{strain_id} has no triage entry with depth 'drop'. Record the triage "
                "verdict first so the drop is confirmed rather than inferred:\n"
                f"  python3 tools/triage.py record --json '{{\"strain_id\": \"{strain_id}\", "
                '"depth": "drop", "triage_notes": "..."}\''
            )

        roster = load_json(path)
        roster["entities"] = [
            e for e in roster.get("entities", []) if e.get("strain_id") != strain_id
        ]
        roster.setdefault("excluded_entities", []).append(
            {
                "strain_id": strain_id,
                "label": display_name(entity),
                "reason": reason.strip(),
            }
        )
        write_json(path, roster)
    return strain_id


def _read_entries(args) -> list[dict]:
    if args.file:
        raw = load_json(args.file)
    elif args.json:
        raw = json.loads(args.json)
    elif sys.stdin.isatty():
        # Waiting on an interactive terminal for JSON looks like a hang, not a prompt.
        raise TriageError("no entries: pass --file or --json, or pipe entries on stdin")
    else:
        raw = json.load(sys.stdin)
    if isinstance(raw, dict):
        # A whole triage.json can be piped in as well as a bare entry.
        raw = raw["triage"] if "triage" in raw else [raw]
    if not isinstance(raw, list):
        raise TriageError("expected an object or a list of objects")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="catalogue root (default: $CATALOGUE_ROOT or repo)")
    sub = parser.add_subparsers(dest="command", required=True)

    record_cmd = sub.add_parser("record", help="upsert triage entries by strain_id")
    source = record_cmd.add_mutually_exclusive_group()
    source.add_argument("--file", help="path to a JSON object or array of entries")
    source.add_argument("--json", help="inline JSON object or array")

    drop_cmd = sub.add_parser("drop", help="move a triaged-as-drop entity off the roster")
    drop_cmd.add_argument("strain_id")
    drop_cmd.add_argument("reason", help="which inclusion criterion failed, and how")

    # --root reads naturally in either position. SUPPRESS keeps a subcommand that
    # omits it from clobbering a value parsed before the subcommand.
    for cmd in (record_cmd, drop_cmd):
        cmd.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    try:
        if args.command == "record":
            recorded = record(args.root, _read_entries(args))
            print(f"recorded {len(recorded)} triage entr{'y' if len(recorded) == 1 else 'ies'}:")
            for strain_id in recorded:
                print(f"  {strain_id}")
        else:
            drop(args.root, args.strain_id, args.reason)
            print(f"{args.strain_id} moved to excluded_entities, strain_id kept")
    except TriageError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, OSError) as exc:
        print(f"could not read input: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
