"""CLI stub for audio → MIDI conversion."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audio-to-midi",
        description="Convert melody audio to a MidiMaster-compatible MIDI file (not implemented yet)",
    )
    sub = parser.add_subparsers(dest="command")

    conv = sub.add_parser("convert", help="Audio file → .mid (planned)")
    conv.add_argument("input", help="Input audio (wav, mp3, flac, …)")
    conv.add_argument("-o", "--output", required=True, help="Output .mid path")
    conv.add_argument(
        "--clef",
        choices=("treble", "bass", "both"),
        default="treble",
        help="Pitch range for the extracted melody",
    )
    conv.add_argument("--bpm", type=float, default=None, help="Override tempo (auto-detect if omitted)")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "convert":
        print(
            "audio_to_midi is scaffolded but not implemented yet.\n"
            "See audio_to_midi/README.md for the planned pipeline.\n"
            f"  Would convert: {args.input} → {args.output} (clef={args.clef})",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
