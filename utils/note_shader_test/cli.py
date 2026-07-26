"""CLI for note_shader_test: list / render / compare / update-goldens."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from note_shader_test.compare import compare_render_to_reference, save_rgba
from note_shader_test.fixtures_io import golden_path_for, iter_cases, load_case
from note_shader_test.harness import GLContextError, NoteShaderHarness, get_harness
from note_shader_test.paths import cases_dir, goldens_dir, notes_frag_path, output_dir


def cmd_list(args: argparse.Namespace) -> int:
    cases = iter_cases(
        atomic_only=bool(getattr(args, "atomic", False)),
        group=getattr(args, "group", None),
    )
    if not cases:
        print(f"No cases in {cases_dir()}")
        return 1
    for c in cases:
        notes = c.get("notes", [])
        group = c.get("group", "")
        atom = "A" if c.get("atomic") else " "
        print(
            f"  [{atom}] {c['name']:52s}  n={len(notes):2d}  "
            f"{group:22s}  {c.get('description', '')}"
        )
    print(f"\n{len(cases)} case(s). Shader: {notes_frag_path()}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    case_path = Path(args.case)
    if not case_path.is_file():
        # bare name: search fixtures/cases recursively
        stem = case_path.stem if case_path.suffix else case_path.name
        matches = list(cases_dir().rglob(f"{stem}.json"))
        if len(matches) == 1:
            case_path = matches[0]
        elif len(matches) > 1:
            print(f"Ambiguous case name {stem!r}: {matches}", file=sys.stderr)
            return 1
        else:
            alt = cases_dir() / case_path
            if not alt.suffix:
                alt = cases_dir() / f"{case_path}.json"
            if alt.is_file():
                case_path = alt
            else:
                print(f"Case not found: {args.case}", file=sys.stderr)
                return 1

    case = load_case(case_path)
    try:
        harness = get_harness(width=args.width, height=args.height)
        image = harness.render_case(case)
    except GLContextError as e:
        print(f"OpenGL unavailable: {e}", file=sys.stderr)
        return 2

    out = Path(args.output) if args.output else output_dir() / f"{case['name']}.png"
    save_rgba(out, image)
    print(f"Wrote {out} ({image.shape[1]}x{image.shape[0]})")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    cases = iter_cases(
        atomic_only=bool(getattr(args, "atomic", False)),
        group=getattr(args, "group", None),
    )
    if args.case:
        cases = [c for c in cases if c["name"] == args.case or Path(c["_path"]).name == args.case]
        if not cases:
            print(f"No matching case: {args.case}", file=sys.stderr)
            return 1

    try:
        harness = get_harness(width=args.width, height=args.height)
    except GLContextError as e:
        print(f"OpenGL unavailable: {e}", file=sys.stderr)
        return 2

    failed = 0
    for case in cases:
        image = harness.render_case(case)
        golden = golden_path_for(case)
        result = compare_render_to_reference(
            case["name"],
            image,
            notes=case.get("notes", []),
            golden_path=golden,
            require_golden=args.require_golden,
            min_region_coverage=args.min_coverage,
        )
        print(result.summary())
        if result.diff_image is not None and not result.passed:
            diff_path = output_dir() / f"{case['name']}_diff.png"
            save_rgba(diff_path, result.diff_image)
            print(f"  wrote diff → {diff_path}")
        if args.save_actual:
            save_rgba(output_dir() / f"{case['name']}_actual.png", image)
        if not result.passed:
            failed += 1

    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


def cmd_update_goldens(args: argparse.Namespace) -> int:
    cases = iter_cases(atomic_only=bool(getattr(args, "atomic", False)))
    if args.case:
        cases = [c for c in cases if c["name"] == args.case]

    try:
        harness = get_harness(width=args.width, height=args.height)
    except GLContextError as e:
        print(f"OpenGL unavailable: {e}", file=sys.stderr)
        return 2

    goldens_dir().mkdir(parents=True, exist_ok=True)
    for case in cases:
        image = harness.render_case(case)
        path = golden_path_for(case)
        save_rgba(path, image)
        print(f"Updated golden {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="note-shader-test",
        description="Verify MidiMaster notes.frag against reference music notation fixtures",
    )
    p.add_argument("--width", type=int, default=960)
    p.add_argument("--height", type=int, default=540)
    sub = p.add_subparsers(dest="command", required=True)

    pl = sub.add_parser("list", help="List fixture cases")
    pl.add_argument("--atomic", action="store_true", help="Only atomic rest/duration cases")
    pl.add_argument("--group", default=None, help="Filter by case group")
    pl.set_defaults(func=cmd_list)

    pr = sub.add_parser("render", help="Render one case to PNG")
    pr.add_argument("case", help="Path or fixture name")
    pr.add_argument("-o", "--output", default=None)
    pr.set_defaults(func=cmd_render)

    pc = sub.add_parser("compare", help="Render all cases and compare to goldens / regions")
    pc.add_argument("--case", default=None, help="Single case name")
    pc.add_argument("--atomic", action="store_true", help="Only atomic rest/duration cases")
    pc.add_argument("--group", default=None, help="Filter by case group")
    pc.add_argument("--require-golden", action="store_true")
    pc.add_argument("--min-coverage", type=float, default=0.04)
    pc.add_argument("--save-actual", action="store_true")
    pc.set_defaults(func=cmd_compare)

    pu = sub.add_parser("update-goldens", help="Overwrite golden PNGs from current shader")
    pu.add_argument("--case", default=None)
    pu.add_argument("--atomic", action="store_true", help="Only atomic cases")
    pu.set_defaults(func=cmd_update_goldens)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
