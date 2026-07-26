"""Map continuous F0 / onsets onto a musical grid and clef range (TODO)."""

from __future__ import annotations

from typing import List, Literal, Tuple

# Approximate clef pitch windows (MIDI). Align with MidiMaster Staff when implementing.
CLEF_RANGES = {
    "treble": (60, 84),   # C4–C6
    "bass": (36, 60),     # C2–C4
    "both": (40, 87),     # Staff.OriginNote .. OriginNote+NumNotes-1
}

Clef = Literal["treble", "bass", "both"]


def filter_midi_to_clef(midi_note: int, clef: Clef) -> bool:
    lo, hi = CLEF_RANGES[clef]
    return lo <= midi_note <= hi


def frames_to_notes(
    times: List[float],
    midi_pitches: List[int],
    *,
    bpm: float,
    clef: Clef = "treble",
) -> List[Tuple[int, int, int]]:
    """
    Convert frame pitch series → list of (midi, start_tick, duration_tick).

    Tick unit should match MidiMaster (32nd notes). Not implemented.
    """
    raise NotImplementedError("quantize.frames_to_notes")
