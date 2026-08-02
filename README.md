# MidiMaster

A rhythm game written in Python that uses musical score notion for display. Currently in-development. Note rendering done in [GLSL for speed](https://www.shadertoy.com/view/7sGcR1) despite supporting notation with a TrueType with freetype. Tested in Python 3.13

## Installation
```bash
python3 -m pip install -r requirements.txt
python3 midimaster.py
```

### Importing MIDI songs

User MIDI always goes into the **Real & Custom Songs** album (files are copied under `music/`).

* **In-game**: Songs menu → **Import MIDI** (file picker; multi-select supported)
* **Command line**:
```bash
python3 midimaster.py --song-add 'The Temptations - My Girl.mid' --song-track 1
python3 midimaster.py --song-add ./my_midis/ --song-track 1
```

### Command line arguments:
Example: 
```bash
python3 midimaster.py --song-add 'The Temptations - My Girl.mid' --song-track 1 --song-default last --debug
```
* `--debug` or `--dev` Run the game in debug mode with the following features:
    1. Print input logging and extra info on the command line
    2. Show FPS and mouse coords on screen
    3. Will load straight into the game screen avoiding the menu system

* `--song-add` Load a MIDI file or folder into **Real & Custom Songs**
* `--song-track` Player track index in the MIDI file (default `1`, the second track)
* `--song-default` Specified which song in the data file is loaded when using debug mode

### Hotkeys:
* Ctrl+D - Toggle dev mode (currently default on)
* PrintScreen - Print out frame timings in dev mode
* Keys ABCDEFG to play MIDI notes Shift is Sharp (#), Ctrl is Flat (b)

## Screenshots
![MidiMaster menu screenshot](https://github.com/macBdog/midimaster/blob/main/screenshot_menu.png?raw=true)
![MidiMaster game screenshot](https://github.com/macBdog/midimaster/blob/main/screenshot_game.png?raw=true)

## Utils (shader tests, audio tools)

Developer tools live under [`utils/`](utils/) (see [utils/README.md](utils/README.md)):

```bash
# Note rendering shader tests (OpenGL required)
pytest utils/note_shader_test/tests -v
python -m note_shader_test compare --atomic   # PYTHONPATH=utils if needed
```

| Tool | Purpose |
|------|---------|
| `utils/note_shader_test` | Offscreen GPU tests for `ext/shaders/notes.frag` vs notation fixtures |
| `utils/audio_to_midi` | (Scaffold) melody audio → MIDI for the game |

## Task Queue:
1. Album unlocks with random songs of ramping difficulty in different keys
2. Temporal accidentals
3. Hook up latency config
