"""CLI for audio → MIDI conversion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audio-to-midi",
        description="Convert melody audio to a MidiMaster-compatible MIDI file",
    )
    sub = parser.add_subparsers(dest="command")

    conv = sub.add_parser("convert", help="Audio file → .mid")
    conv.add_argument("input", help="Input audio (wav, mp3, flac, …)")
    conv.add_argument("-o", "--output", required=True, help="Output .mid path")
    conv.add_argument(
        "--clef",
        choices=("treble", "bass", "both"),
        default="treble",
        help="Pitch range for the extracted melody (default: treble)",
    )
    conv.add_argument(
        "--bpm",
        type=float,
        default=None,
        help="Optional tempo override (default: auto-detect and pin from audio)",
    )
    conv.add_argument(
        "--sr",
        type=int,
        default=22050,
        help="Analysis sample rate (default: 22050)",
    )

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "convert":
        from audio_to_midi.convert import convert

        try:
            result = convert(
                args.input,
                args.output,
                clef=args.clef,
                bpm=args.bpm,
                sr=args.sr,
            )
        except ImportError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"error: conversion failed: {exc}", file=sys.stderr)
            return 1

        src = "auto-detected" if result.bpm_source == "auto" else "override"
        print(f"Wrote {Path(result.path).resolve()}")
        print(f"  tempo: {result.bpm:g} BPM ({src})")
        print(f"  notes: {result.note_count}  clef: {result.clef}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
