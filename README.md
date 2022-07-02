# MidiMaster

A rhythm game written in Python that uses musical score notion for display. Currently in-development. Note rendering done in [GLSL for speed](https://www.shadertoy.com/view/7sGcR1) despite supporting notation with a TrueType with freetype.

## Installation
```bash
python3 -m pip install -r requirements.txt
python3 midimaster.py
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

* `--song-add` Will load a specified Midi file or folder of files into the game data
* `--song-track` Specifies which track of the input midi file is used for player info. Default is 1 (the second track)
* `--song-default` Specified which song in the data file is loaded when using debug mode

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