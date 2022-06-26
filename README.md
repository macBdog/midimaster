# MidiMaster

A rhythm game written in Python that uses musical score notion for display. Currently in-development. Note rendering done in [GLSL for speed](https://www.shadertoy.com/view/7sGcR1) despite supporting notation with a TrueType with freetype.

## Installation
```bash
python3 -m pip install -r requirements.txt
python3 midimaster.py
```

### Hotkeys:
* Ctrl+D - Toggle dev mode (currently default on)
* PrintScreen - Print out frame timings in dev mode
* Keys ABCDEFG to play MIDI notes Shift is Sharp (#), Ctrl is Flat (b)

## Task Queue:
1. Temporal accidentals
2. Device selection
3. 3 strikes system
4. Song selection data file
5. Main menu GUI
6. Game submodule with hot reload shaders