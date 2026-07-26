"""Top-level convert API: audio file → MidiMaster-compatible MIDI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from audio_to_midi.midi_write import write_melody_midi
from audio_to_midi.pitch_track import estimate_bpm, estimate_f0, load_audio, pin_bpm
from audio_to_midi.quantize import frames_to_notes

Clef = Literal["treble", "bass", "both"]
NoteEvent = Tuple[int, int, int]


@dataclass(frozen=True)
class ConvertResult:
    """Result of a conversion, including the auto-detected tempo."""

    path: Path
    bpm: float
    bpm_source: str  # "auto" | "override"
    note_count: int
    clef: str

    def __fspath__(self) -> str:
        return str(self.path)


def convert(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    clef: Clef = "treble",
    bpm: Optional[float] = None,
    sr: int = 22050,
) -> ConvertResult:
    """
    Extract the main melody from *input_path* and write a MIDI file.

    Tempo is **always pinned automatically** from the audio unless *bpm* is
    passed as an explicit override (then it is still normalized via ``pin_bpm``).

    Parameters
    ----------
    input_path:
        Audio file (wav/mp3/flac/ogg — requires librosa).
    output_path:
        Destination ``.mid`` path.
    clef:
        Pitch window: ``treble`` (E3–F5), ``bass``, or ``both`` (full staff).
    bpm:
        Optional tempo override. When omitted (default), tempo is detected
        and pinned automatically.
    sr:
        Analysis sample rate.

    Returns
    -------
    ConvertResult
        Output path, pinned BPM, and note count.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    audio, file_sr = load_audio(input_path, sr=sr, mono=True)
    if audio.size == 0:
        raise ValueError(f"Empty audio: {input_path}")

    if bpm is None:
        tempo = estimate_bpm(audio, file_sr)
        bpm_source = "auto"
    else:
        tempo = pin_bpm(float(bpm))
        bpm_source = "override"

    times, f0 = estimate_f0(audio, file_sr)
    if times.size == 0:
        raise ValueError(f"Could not analyze audio: {input_path}")

    notes: List[NoteEvent] = frames_to_notes(times, f0, bpm=tempo, clef=clef)
    if not notes:
        raise ValueError(
            f"No pitched notes detected in {input_path.name}. "
            "Try a clearer monophonic source or isolated vocal stem."
        )

    path = write_melody_midi(notes, output_path, bpm=tempo)
    return ConvertResult(
        path=path,
        bpm=tempo,
        bpm_source=bpm_source,
        note_count=len(notes),
        clef=clef,
    )
