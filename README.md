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
1. Fix all note rendering
2. Temporal accidentals
3. Device selection
4. Note length animation bar
5. Song selection data file
6. GUI
7. Hot reload shaders