"""Map continuous F0 / onsets onto a musical grid and clef range."""

from __future__ import annotations

from typing import List, Literal, Optional, Sequence, Tuple

import numpy as np

# Align with MidiMaster staff + procedural_songs clef limits
CLEF_RANGES = {
    "treble": (52, 77),  # E3–F5 (displayable treble)
    "bass": (40, 60),    # E2–C4 (placeholder until bass clef exists)
    "both": (40, 87),    # Staff.OriginNote .. OriginNote+NumNotes-1
}

Clef = Literal["treble", "bass", "both"]

# MidiMaster uses 8 thirty-second notes per beat
SDQ_NOTES_PER_BEAT = 8
MIN_NOTE_LENGTH_32S = 2

NoteEvent = Tuple[int, int, int]  # midi, start_tick_32s, duration_tick_32s


def filter_midi_to_clef(midi_note: int, clef: Clef) -> bool:
    lo, hi = CLEF_RANGES[clef]
    return lo <= midi_note <= hi


def clamp_midi_to_clef(midi_note: int, clef: Clef) -> int:
    """Octave-shift *midi_note* into the clef window when possible."""
    lo, hi = CLEF_RANGES[clef]
    n = int(midi_note)
    while n < lo:
        n += 12
    while n > hi:
        n -= 12
    if n < lo:
        n = max(lo, min(hi, n))
    return n


def hz_to_midi(hz: float) -> Optional[int]:
    """Convert frequency to nearest MIDI note number, or None if unvoiced."""
    if hz is None or hz <= 0.0 or not np.isfinite(hz):
        return None
    midi = 69.0 + 12.0 * np.log2(float(hz) / 440.0)
    return int(round(midi))


def frames_to_notes(
    times: Sequence[float],
    f0_hz: Sequence[float],
    *,
    bpm: float,
    clef: Clef = "treble",
    min_note_sec: float = 0.08,
    pitch_hold_frames: int = 2,
    clamp_out_of_range: bool = True,
) -> List[NoteEvent]:
    """
    Convert frame pitch series → list of ``(midi, start_32nd, duration_32nd)``.

    Tick unit matches MidiMaster song time (thirty-second notes).
    """
    if bpm <= 0:
        raise ValueError("bpm must be positive")

    times_a = np.asarray(times, dtype=np.float64)
    f0_a = np.asarray(f0_hz, dtype=np.float64)
    if times_a.size == 0 or f0_a.size == 0:
        return []
    if times_a.size != f0_a.size:
        n = min(times_a.size, f0_a.size)
        times_a = times_a[:n]
        f0_a = f0_a[:n]

    # Frame → MIDI (0 = unvoiced)
    midi_frames: List[int] = []
    for hz in f0_a:
        m = hz_to_midi(float(hz))
        midi_frames.append(0 if m is None else int(m))

    # Median filter-ish: require pitch_hold_frames consistency via run-length later
    sec_per_32nd = 60.0 / (float(bpm) * SDQ_NOTES_PER_BEAT)

    raw_notes: List[Tuple[int, float, float]] = []  # midi, start_sec, end_sec
    i = 0
    n = len(midi_frames)
    while i < n:
        pitch = midi_frames[i]
        if pitch <= 0:
            i += 1
            continue
        j = i + 1
        while j < n and midi_frames[j] == pitch:
            j += 1
        # Allow 1-frame holes inside a note
        while j < n - 1 and midi_frames[j] == 0 and midi_frames[j + 1] == pitch:
            j += 2
            while j < n and midi_frames[j] == pitch:
                j += 1

        run_len = j - i
        if run_len < pitch_hold_frames:
            i = j
            continue

        t0 = float(times_a[i])
        t1 = float(times_a[min(j - 1, n - 1)])
        # Extend end by roughly one hop so short notes keep body
        if j < n:
            t1 = max(t1, float(times_a[j - 1]) + (times_a[1] - times_a[0] if n > 1 else 0.02))
        else:
            t1 = t1 + 0.02

        if (t1 - t0) < min_note_sec:
            i = j
            continue

        midi = pitch
        if not filter_midi_to_clef(midi, clef):
            if clamp_out_of_range:
                midi = clamp_midi_to_clef(midi, clef)
            else:
                i = j
                continue

        raw_notes.append((midi, t0, t1))
        i = j

    # Merge adjacent same-pitch notes with tiny gaps
    merged: List[Tuple[int, float, float]] = []
    for midi, t0, t1 in raw_notes:
        if merged and merged[-1][0] == midi and t0 - merged[-1][2] <= 0.06:
            prev = merged[-1]
            merged[-1] = (prev[0], prev[1], max(prev[2], t1))
        else:
            merged.append((midi, t0, t1))

    # Quantize to 32nd grid
    notes: List[NoteEvent] = []
    for midi, t0, t1 in merged:
        start_32 = int(round(t0 / sec_per_32nd))
        end_32 = int(round(t1 / sec_per_32nd))
        dur = max(MIN_NOTE_LENGTH_32S, end_32 - start_32)
        # Avoid zero-length overlap pile-ups: push start if needed
        if notes and start_32 < notes[-1][1] + notes[-1][2]:
            # Allow polyphony-free monophonic stream: clip previous or shift
            prev_midi, prev_start, prev_dur = notes[-1]
            prev_end = prev_start + prev_dur
            if start_32 < prev_end:
                new_prev_dur = max(MIN_NOTE_LENGTH_32S, start_32 - prev_start)
                notes[-1] = (prev_midi, prev_start, new_prev_dur)
        notes.append((midi, max(0, start_32), dur))

    return notes


def seconds_to_32nds(seconds: float, bpm: float) -> int:
    sec_per_32nd = 60.0 / (float(bpm) * SDQ_NOTES_PER_BEAT)
    return int(round(seconds / sec_per_32nd))
