"""Top-level convert API (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

Clef = Literal["treble", "bass", "both"]


def convert(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    clef: Clef = "treble",
    bpm: Optional[float] = None,
) -> Path:
    """
    Extract the main melody from *input_path* and write a MIDI file.

    Not implemented — raises NotImplementedError.
    """
    raise NotImplementedError(
        "audio_to_midi.convert is not implemented yet. "
        "See audio_to_midi/README.md for the planned pipeline."
    )
