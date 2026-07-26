"""Write melody note list to a standard MIDI file (mido)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple, Union

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

NoteEvent = Tuple[int, int, int]  # midi, start_32nd, duration_32nd

# Match MidiMaster song timing: 8 thirty-second notes per beat
SDQ_NOTES_PER_BEAT = 8
DEFAULT_VELOCITY = 100  # above Song.MinVelocity (64)


def write_melody_midi(
    notes: Sequence[NoteEvent],
    output_path: Union[str, Path],
    *,
    bpm: float = 120.0,
    ticks_per_beat: int = 480,
    program: int = 0,
) -> Path:
    """
    Write a single-track MIDI file loadable by MidiMaster.

    *notes* use MidiMaster 32nd-note time units for start/duration.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(bpm), time=0))
    track.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    track.append(MetaMessage("track_name", name="Melody", time=0))
    track.append(Message("program_change", program=program, time=0))

    # Convert 32nd units → MIDI ticks
    # ticks_per_32nd = ticks_per_beat / 8
    ticks_per_32nd = ticks_per_beat / float(SDQ_NOTES_PER_BEAT)

    # Build absolute on/off events then emit delta times
    events: List[Tuple[int, str, int]] = []  # tick, type, midi
    for midi, start_32, dur_32 in notes:
        if dur_32 <= 0:
            continue
        midi = int(max(0, min(127, midi)))
        on_tick = int(round(start_32 * ticks_per_32nd))
        off_tick = int(round((start_32 + dur_32) * ticks_per_32nd))
        if off_tick <= on_tick:
            off_tick = on_tick + max(1, int(round(ticks_per_32nd)))
        events.append((on_tick, "on", midi))
        events.append((off_tick, "off", midi))

    events.sort(key=lambda e: (e[0], 0 if e[1] == "off" else 1, e[2]))

    last_tick = 0
    for tick, kind, midi in events:
        delta = max(0, tick - last_tick)
        if kind == "on":
            track.append(
                Message("note_on", note=midi, velocity=DEFAULT_VELOCITY, time=delta)
            )
        else:
            track.append(Message("note_off", note=midi, velocity=0, time=delta))
        last_tick = tick

    # Trailing silence so the file has a clean end
    track.append(MetaMessage("end_of_track", time=ticks_per_beat))

    mid.save(str(output_path))
    return output_path
