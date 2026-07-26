"""Write melody note list to a standard MIDI file (TODO)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple, Union

NoteEvent = Tuple[int, int, int]  # midi, start_tick, duration_tick


def write_melody_midi(
    notes: Sequence[NoteEvent],
    output_path: Union[str, Path],
    *,
    bpm: float = 120.0,
    ticks_per_beat: int = 480,
) -> Path:
    """
    Write a single-track MIDI file loadable by MidiMaster.

    Not implemented — use mido when building this out.
    """
    raise NotImplementedError("midi_write.write_melody_midi")
