# utils

Developer utilities and support tools for MidiMaster (pitchfork-style `utils/` tree).

| Tool | Status | Purpose |
|------|--------|---------|
| **note_shader_test** | Implemented | Offscreen-render `ext/shaders/notes.frag` against notation fixtures (incl. atomic rest/duration cases) |
| **audio_to_midi** | Implemented | Convert melody audio → MIDI playable in MidiMaster |

## Layout

```
midimaster/
  ext/shaders/notes.frag     # production shader under test
  tests/                     # game unit tests (latency, etc.)
  utils/                     # this tree — standalone tools + their fixtures/tests
    note_shader_test/
    audio_to_midi/
    output/                  # local render dumps (gitignored)
```

## note_shader_test

From the **midimaster repo root**:

```bash
# Ensure utils is on PYTHONPATH (pytest.ini sets this for pytest)
pip install Pillow  # if not already available

pytest utils/note_shader_test/tests -v

# CLI
python -m note_shader_test list --atomic
python -m note_shader_test compare --atomic
python -m note_shader_test render atom_rest_only_quarter -o utils/output/q.png
python -m note_shader_test update-goldens --atomic

# Regenerate atomic JSON fixtures after editing the catalog
python -m note_shader_test.atomic_catalog write
```

If `python -m note_shader_test` cannot find the package, set:

```bash
# Windows PowerShell
$env:PYTHONPATH = "utils"
# Unix
export PYTHONPATH=utils
```

Optional env overrides:

- `MIDIMASTER_ROOT` — rarely needed (defaults to parent of `utils/`)
- `GAMEJAM_ROOT` — path to gamejam for `texture.vert` (defaults to `../gamejam`)

### Atomic rest + duration suite

Hard renderer cases live one-per-file under `note_shader_test/fixtures/cases/atomic/`.  
See `note_shader_test/atomic_catalog.py` and filter with `pytest -k atom_…`.

## audio_to_midi

Melody audio → MidiMaster-compatible MIDI. See [audio_to_midi/README.md](audio_to_midi/README.md).

```bash
# Utility-only deps (not required by the game)
pip install -r utils/audio_to_midi/requirements.txt

$env:PYTHONPATH = "utils"   # Windows PowerShell
python -m audio_to_midi convert song.wav -o song.mid --clef treble
# tempo is auto-detected and pinned; --bpm only to override
pytest utils/audio_to_midi/tests -v
```
