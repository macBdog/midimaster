"""
Atomic rest + duration fixture catalog.

Each case is one isolated rendering scenario so a failing test points at a
single glyph / sequence problem (not a pile of overlapping durations).

Regenerate JSON on disk::

    python -m note_shader_test.atomic_catalog write
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from note_shader_test.paths import cases_dir

# G4 — mid-staff white key; stems go down (above midline). Keeps duration
# geometry free of ledger-line noise. Override per-case when needed.
DEFAULT_MIDI = 67

# Horizontal slots (NDC). Wide enough that flags / rest glyphs don't collide.
X0 = -0.36
X1 = 0.0
X2 = 0.36
X_SOLO = 0.0

DURATIONS: Sequence[str] = (
    "whole",
    "half",
    "quarter",
    "eighth",
    "sixteenth",
    "thirtysecond",
)

# Dotted durations that MidiMaster actually draws (decoration dotted on head)
DOTTED_DURATIONS: Sequence[str] = ("whole", "half", "quarter", "eighth")

# Cross-length pairs: (left_type, right_type) without "rest_" prefix on notes
# These are the hard spacing / glyph-neighbour cases.
CROSS_NOTE_REST: Sequence[tuple[str, str]] = (
    ("quarter", "eighth"),
    ("quarter", "sixteenth"),
    ("quarter", "half"),
    ("eighth", "quarter"),
    ("eighth", "sixteenth"),
    ("sixteenth", "eighth"),
    ("sixteenth", "quarter"),
    ("half", "quarter"),
    ("half", "eighth"),
    ("whole", "quarter"),
    ("whole", "half"),
    ("thirtysecond", "eighth"),
    ("eighth", "thirtysecond"),
)

CROSS_REST_NOTE: Sequence[tuple[str, str]] = (
    ("eighth", "quarter"),
    ("sixteenth", "quarter"),
    ("quarter", "eighth"),
    ("half", "quarter"),
    ("quarter", "half"),
    ("sixteenth", "eighth"),
    ("eighth", "sixteenth"),
)

# Two different pitched note lengths side-by-side (no rest) — flag vs head
CROSS_NOTE_NOTE: Sequence[tuple[str, str]] = (
    ("quarter", "eighth"),
    ("eighth", "quarter"),
    ("half", "quarter"),
    ("quarter", "half"),
    ("eighth", "sixteenth"),
    ("sixteenth", "eighth"),
    ("whole", "half"),
    ("half", "whole"),
    ("sixteenth", "thirtysecond"),
    ("thirtysecond", "sixteenth"),
)


def _note(midi: int, x: float, ntype: str, **extra: Any) -> dict:
    d: Dict[str, Any] = {
        "midi": midi,
        "x": x,
        "type": ntype,
        "decoration": extra.pop("decoration", "none"),
        "colour": [0.11, 0.11, 0.11, 1.0],
    }
    d.update(extra)
    return d


def _rest(x: float, ntype: str) -> dict:
    # midi is ignored for rest glyph Y (shader uses staff_pos); kept for tooling
    return _note(DEFAULT_MIDI, x, ntype if ntype.startswith("rest_") else f"rest_{ntype}")


def _case(
    name: str,
    description: str,
    notes: List[dict],
    *,
    tags: Sequence[str],
    group: str,
) -> Dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "group": group,
        "tags": list(tags),
        "atomic": True,
        "note_names": False,
        "music_time": 0.0,
        "notes": notes,
        "golden": name,
    }


def build_catalog() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ rests only
    for d in DURATIONS:
        cases.append(
            _case(
                f"atom_rest_only_{d}",
                f"Single {d} rest alone on staff — isolate rest glyph",
                [_rest(X_SOLO, d)],
                tags=("atomic", "rest", "solo", d),
                group="rest_solo",
            )
        )

    # ------------------------------------------------------------------ notes only
    for d in DURATIONS:
        cases.append(
            _case(
                f"atom_note_only_{d}",
                f"Single {d} note (G4) — isolate head/stem/flag for this duration",
                [_note(DEFAULT_MIDI, X_SOLO, d)],
                tags=("atomic", "note", "solo", d),
                group="note_solo",
            )
        )

    for d in DOTTED_DURATIONS:
        cases.append(
            _case(
                f"atom_note_only_{d}_dotted",
                f"Single dotted {d} note (G4) — isolate augmentation dot",
                [_note(DEFAULT_MIDI, X_SOLO, d, decoration="dotted")],
                tags=("atomic", "note", "solo", "dotted", d),
                group="note_dotted",
            )
        )

    # ------------------------------------------------------------------ same length: note then rest
    for d in DURATIONS:
        cases.append(
            _case(
                f"atom_seq_note_{d}_rest_{d}",
                f"{d} note then {d} rest — same-length succession",
                [_note(DEFAULT_MIDI, X0, d), _rest(X1, d)],
                tags=("atomic", "sequence", "note_rest", "same_length", d),
                group="seq_note_rest_same",
            )
        )

    # ------------------------------------------------------------------ same length: rest then note
    for d in DURATIONS:
        cases.append(
            _case(
                f"atom_seq_rest_{d}_note_{d}",
                f"{d} rest then {d} note — rest-leading same length",
                [_rest(X0, d), _note(DEFAULT_MIDI, X1, d)],
                tags=("atomic", "sequence", "rest_note", "same_length", d),
                group="seq_rest_note_same",
            )
        )

    # ------------------------------------------------------------------ cross: note then different rest
    for note_d, rest_d in CROSS_NOTE_REST:
        if note_d == rest_d:
            continue
        cases.append(
            _case(
                f"atom_seq_note_{note_d}_rest_{rest_d}",
                f"{note_d} note then {rest_d} rest — mixed durations",
                [_note(DEFAULT_MIDI, X0, note_d), _rest(X1, rest_d)],
                tags=("atomic", "sequence", "note_rest", "cross_length", note_d, rest_d),
                group="seq_note_rest_cross",
            )
        )

    # ------------------------------------------------------------------ cross: rest then different note
    for rest_d, note_d in CROSS_REST_NOTE:
        if rest_d == note_d:
            continue
        cases.append(
            _case(
                f"atom_seq_rest_{rest_d}_note_{note_d}",
                f"{rest_d} rest then {note_d} note — mixed durations",
                [_rest(X0, rest_d), _note(DEFAULT_MIDI, X1, note_d)],
                tags=("atomic", "sequence", "rest_note", "cross_length", rest_d, note_d),
                group="seq_rest_note_cross",
            )
        )

    # ------------------------------------------------------------------ two notes different lengths (no rest)
    for a, b in CROSS_NOTE_NOTE:
        if a == b:
            continue
        cases.append(
            _case(
                f"atom_seq_note_{a}_note_{b}",
                f"{a} note then {b} note — juxtaposed durations (flags/stems)",
                [_note(DEFAULT_MIDI, X0, a), _note(DEFAULT_MIDI, X1, b)],
                tags=("atomic", "sequence", "note_note", "cross_length", a, b),
                group="seq_note_note_cross",
            )
        )

    # ------------------------------------------------------------------ three-event atomic patterns
    three = [
        (
            "atom_seq_note_quarter_rest_eighth_note_eighth",
            "quarter + eighth-rest + eighth — common fill after a beat",
            [
                _note(DEFAULT_MIDI, X0, "quarter"),
                _rest(X1, "eighth"),
                _note(DEFAULT_MIDI, X2, "eighth"),
            ],
            ("quarter", "eighth"),
        ),
        (
            "atom_seq_note_eighth_rest_eighth_note_eighth",
            "eighth + eighth-rest + eighth — short-rest interruption",
            [
                _note(DEFAULT_MIDI, X0, "eighth"),
                _rest(X1, "eighth"),
                _note(DEFAULT_MIDI, X2, "eighth"),
            ],
            ("eighth",),
        ),
        (
            "atom_seq_rest_quarter_note_eighth_note_eighth",
            "quarter-rest + two eighths (unbeamed) — pickup after rest",
            [
                _rest(X0, "quarter"),
                _note(DEFAULT_MIDI, X1, "eighth"),
                _note(DEFAULT_MIDI, X2, "eighth"),
            ],
            ("quarter", "eighth"),
        ),
        (
            "atom_seq_note_eighth_note_eighth_rest_quarter",
            "two eighths (unbeamed) + quarter rest — phrase end",
            [
                _note(DEFAULT_MIDI, X0, "eighth"),
                _note(DEFAULT_MIDI, X1, "eighth"),
                _rest(X2, "quarter"),
            ],
            ("eighth", "quarter"),
        ),
        (
            "atom_seq_note_sixteenth_rest_sixteenth_note_eighth",
            "sixteenth + sixteenth-rest + eighth — nested short values",
            [
                _note(DEFAULT_MIDI, X0, "sixteenth"),
                _rest(X1, "sixteenth"),
                _note(DEFAULT_MIDI, X2, "eighth"),
            ],
            ("sixteenth", "eighth"),
        ),
        (
            "atom_seq_note_half_rest_quarter_note_quarter",
            "half + quarter-rest + quarter — long then short fill",
            [
                _note(DEFAULT_MIDI, X0, "half"),
                _rest(X1, "quarter"),
                _note(DEFAULT_MIDI, X2, "quarter"),
            ],
            ("half", "quarter"),
        ),
        (
            "atom_seq_rest_eighth_note_sixteenth_note_sixteenth",
            "eighth-rest + two sixteenths (unbeamed) — short pickup",
            [
                _rest(X0, "eighth"),
                _note(DEFAULT_MIDI, X1, "sixteenth"),
                _note(DEFAULT_MIDI, X2, "sixteenth"),
            ],
            ("eighth", "sixteenth"),
        ),
        (
            "atom_seq_note_quarter_rest_sixteenth_note_sixteenth",
            "quarter + sixteenth-rest + sixteenth — partial beat fill",
            [
                _note(DEFAULT_MIDI, X0, "quarter"),
                _rest(X1, "sixteenth"),
                _note(DEFAULT_MIDI, X2, "sixteenth"),
            ],
            ("quarter", "sixteenth"),
        ),
    ]
    for name, desc, notes, durs in three:
        cases.append(
            _case(
                name,
                desc,
                notes,
                tags=["atomic", "sequence", "three_event", *durs],
                group="seq_three",
            )
        )

    # Stem-up duration isolates (C4) — flags/stems opposite of G4
    for d in ("quarter", "eighth", "sixteenth", "thirtysecond"):
        cases.append(
            _case(
                f"atom_note_only_{d}_stem_up",
                f"Single {d} on C4 (stem up) — duration with opposite stem",
                [_note(60, X_SOLO, d)],
                tags=("atomic", "note", "solo", "stem_up", d),
                group="note_solo_stem_up",
            )
        )

    # Ensure unique names
    names = [c["name"] for c in cases]
    assert len(names) == len(set(names)), "duplicate atomic case names"

    return cases


def atomic_cases() -> List[Dict[str, Any]]:
    return build_catalog()


def atomic_case_names() -> List[str]:
    return [c["name"] for c in build_catalog()]


def cases_by_group() -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for c in build_catalog():
        out.setdefault(c["group"], []).append(c)
    return out


def write_fixture_files(directory: Path | None = None) -> List[Path]:
    """Write one JSON file per atomic case under fixtures/cases/atomic/."""
    root = directory or (cases_dir() / "atomic")
    root.mkdir(parents=True, exist_ok=True)
    # Remove stale atom_*.json so renames don't leave orphans
    for old in root.glob("atom_*.json"):
        old.unlink()

    written: List[Path] = []
    for case in build_catalog():
        # Disk payload omits runtime-only keys later re-added by load_case
        payload = {k: v for k, v in case.items() if not k.startswith("_")}
        path = root / f"{case['name']}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def main(argv: List[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Atomic rest/duration fixture catalog")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="Print case names and groups")
    sub.add_parser("write", help="Write JSON fixtures under fixtures/cases/atomic/")
    sub.add_parser("count", help="Print case counts by group")
    args = p.parse_args(argv)

    if args.cmd == "list":
        for c in build_catalog():
            print(f"{c['group']:24s}  {c['name']:55s}  {c['description']}")
        return 0
    if args.cmd == "count":
        groups = cases_by_group()
        total = 0
        for g, items in sorted(groups.items()):
            print(f"{g:24s}  {len(items):3d}")
            total += len(items)
        print(f"{'TOTAL':24s}  {total:3d}")
        return 0
    if args.cmd == "write":
        paths = write_fixture_files()
        print(f"Wrote {len(paths)} fixtures to {paths[0].parent}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
