# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

MidiMaster is a Python rhythm game that displays musical notation and accepts MIDI input. Players read scrolling sheet music and play notes on a MIDI device (or keyboard). The game uses OpenGL for rendering with custom GLSL shaders for high-performance note display.

## Build & Run Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Install gamejam framework (required, install editable from separate repo)
pip install -e path/to/gamejam

# Run the game
python midimaster.py

# Run in debug/dev mode (loads directly into game screen, shows FPS/coords)
python midimaster.py --debug

# Add a MIDI file to the songbook
python midimaster.py --song-add "path/to/song.mid" --song-track 1

# Add a folder of MIDI files
python midimaster.py --song-add "path/to/folder/" --song-track 1

# Run tests (pytest)
pytest tests/
```

## Architecture

### Core Game Loop

`MidiMaster` (in `midimaster.py`) extends `GameJam` framework and orchestrates:
- **prepare()**: Initializes songbook, MIDI devices, menu system, staff display, and note renderer
- **update(dt)**: Main game loop - processes MIDI input, updates music playback, handles scoring
- **end()**: Saves songbook state and closes MIDI connections

### Music Data Pipeline

```
Song (MIDI file) → Notes (decorated for display) → NoteRender (GPU rendering)
```

1. **Song** (`song.py`): Parses MIDI files via `mido`, extracts notes, tempo, time signature, key signature. Stores player track separately from backing tracks.

2. **Notes** (`notes.py`): Post-processes raw notes - adds rests, calculates note types (whole/half/quarter/etc), handles accidentals via KeySignature, manages "hats" (beamed eighth/sixteenth note groupings).

3. **NoteRender** (`note_render.py`): GPU-based rendering using custom fragment shader (`ext/shaders/notes.frag`). Maintains a pool of 32 active notes, uploads positions/colors/types as uniforms each frame.

### MIDI Handling

- **MidiDevices** (`midi_devices.py`): Manages MIDI I/O via `mido` and `python-rtmidi`. Maintains separate input/output message queues.
- Input messages from player are echoed to output for audio feedback
- Backing tracks are played in sync with game time

### Display Coordinates

The game uses normalized device coordinates (-1 to 1):
- Staff position: `Staff.Pos = [-1.0 + (2.0 - 1.85), 0.0]` (right-aligned, 1.85 width)
- Notes scroll right-to-left, hitting playhead at staff origin
- `note_positions` dict maps MIDI note numbers to Y coordinates

### Menu System

`Menu` (`menu.py`) manages screen states via `Menus` enum:
- `SPLASH`: Animated title screen
- `SONGS`: Album/song browser with scrolling list
- `GAME`: Main gameplay screen

Dialogs: `DEVICES` (MIDI config), `GAME_OVER` (score display)

### Persistence

`SongBook` (`song_book.py`): Pickle-serialized save file (`ext/songs.pkl`) storing:
- Albums containing Songs with player scores
- Preferred MIDI device names
- Default song selection

### Scoring

Two modes in `MusicMode`:
- `PERFORMANCE`: Score based on timing accuracy
- `PAUSE_AND_LEARN`: Music pauses until player plays correct note

Score thresholds for trophies: 55%, 70%, 90% of max score.

## Key Constants

- `Staff.OriginNote = 40` (E2) - lowest playable note
- `Staff.NumNotes = 48` - playable range
- `Song.SDQNotesPerBeat = 8` - 32nd notes per beat
- `NoteRender.NumNotes = 32` - GPU note pool size

## External Dependencies

- **gamejam**: Custom game framework (not on PyPI - requires separate installation as editable package). Provides Graphics, GUI, Input, Font, Animation systems.
- **mido/python-rtmidi**: MIDI file parsing and device I/O
- **PyOpenGL/glfw**: OpenGL rendering
- **numpy**: Array operations

## Hotkeys (In-Game)

- Space: Pause/resume
- A-G keys: Play notes (Shift=sharp, Ctrl=flat)
- Arrow keys: Scrub through music time
- +/-: Adjust note spacing
- Ctrl+D: Toggle dev mode
- PrintScreen: Print frame timings (dev mode)
