# audio_to_midi

Convert a monophonic (or melody-dominant) audio file into a MIDI file that MidiMaster can load and play along to.

## Status

**Implemented** — monophonic melody extraction with librosa F0, automatic tempo detection/pinning, clef filtering, and 32nd-note quantization.

## Install (utility only)

These deps are **not** required by the MidiMaster game. Install them only for this tool:

```bash
pip install -r utils/audio_to_midi/requirements.txt
```

Contents: `librosa`, `soundfile`, plus `numpy` / `mido` if missing.

## CLI

From the **midimaster repo root**:

```bash
# Windows PowerShell
$env:PYTHONPATH = "utils"

python -m audio_to_midi convert song.wav -o song.mid --clef treble
python -m audio_to_midi convert song.mp3 -o song.mid --clef both
```

Tempo is **auto-detected and pinned** from the audio (half/double-time corrected, rounded).  
Optional `--bpm` only if you need a manual override.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `input` | required | Audio path |
| `-o` / `--output` | required | Output `.mid` path |
| `--clef` | `treble` | `treble` (E3–F5), `bass` (E2–C4), or `both` (full staff) |
| `--bpm` | auto | Optional tempo override (still pinned/normalized) |
| `--sr` | 22050 | Analysis sample rate |

## Python API

```python
from audio_to_midi import convert

result = convert("melody.wav", "melody.mid", clef="treble")
print(result.path, result.bpm, result.note_count)
```

## Pipeline

1. **Load audio** — librosa (+ soundfile backends)
2. **Tempo** — onset strength + beat track, half/double correction, pin to 0.1 BPM
3. **Melody F0** — `librosa.pyin`
4. **Segment** — stable voiced runs → note on/off
5. **Clef filter** — clamp into selected range
6. **Quantize** — thirty-second-note grid (MidiMaster time)
7. **Write MIDI** — single melody track via `mido`

## Layout

```
audio_to_midi/
  requirements.txt  # librosa + soundfile (this util only)
  README.md
  convert.py
  pitch_track.py
  quantize.py
  midi_write.py
  cli.py
  tests/
```

## MidiMaster integration

- Load the `.mid` via `Song.from_midi_file` / the song menu.
- One track, melody only; prefer `--clef treble` for the current single staff.

## Tests

```bash
$env:PYTHONPATH = "utils"
pytest utils/audio_to_midi/tests -v
```
