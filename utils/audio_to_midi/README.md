# audio_to_midi

Convert a monophonic (or melody-dominant) audio file into a MIDI file that MidiMaster can load and play along to.

## Status

**Scaffold only** — not implemented yet. Folder layout and interfaces are placeholders for the first real implementation.

## Goals

| Input | Output |
|-------|--------|
| `.wav`, `.mp3`, `.flac`, `.ogg`, … | Standard MIDI (`.mid`) with the main melody |

- Pitch range limited to **treble clef**, **bass clef**, or **both** (user choice)
- Rhythm quantized to musical grid (suitable for MidiMaster’s 32nd-note timing)
- Single melodic line preferred (humming, solo instrument, isolated vocal)

## Planned CLI

```bash
# Not implemented yet
python -m audio_to_midi convert song.mp3 -o song.mid --clef treble
python -m audio_to_midi convert song.wav -o song.mid --clef both --bpm 120
```

## Planned pipeline

1. **Load audio** — `librosa` / `soundfile` (resample to analysis rate)
2. **Melody estimate** — pYIN / CREPE / librosa `piptrack` or similar F0 tracker
3. **Clef filter** — drop or clamp pitches outside:
   - Treble-focused: ~MIDI 60–84 (C4–C6) or staff range MidiMaster draws
   - Bass-focused: ~MIDI 36–60
   - Both: MidiMaster playable range (see `Staff.OriginNote` / `NumNotes`)
4. **Note segmentation** — voiced frames → note on/off with minimum duration
5. **Quantize** — map onsets/durations to MidiMaster’s 32nd-note units
6. **Write MIDI** — `mido` or `pretty_midi`, channel 0 melody, tempo meta
7. **Validate** — load with midimaster’s song path / smoke-play

## Layout (this package)

```
audio_to_midi/
  README.md           # this file
  __init__.py
  __main__.py         # entry: python -m audio_to_midi
  cli.py              # argparse stub
  convert.py          # convert() stub
  pitch_track.py      # F0 estimation (TODO)
  quantize.py         # grid / clef filtering (TODO)
  midi_write.py       # mido export (TODO)
  samples/            # optional short test clips (not committed large binaries)
  tests/              # unit tests (TODO)
```

## MidiMaster integration notes

- MidiMaster loads MIDI via its song / album pipeline (`music.py`, `song.py`).
- Prefer one track, melody only, no percussion.
- Note numbers must fall in `Staff` playable range or they are ignored at decorate time (`notes.py`).

## Dependencies (when implementing)

```
pip install midimaster-utils[audio]
# or: librosa soundfile mido pretty_midi
```
