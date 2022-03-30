from mido import MidiFile
from mido import MetaMessage
from mido import Message
from notes import Note
from notes import Notes
from font import Font
from graphics import Graphics
from texture import TextureManager
import math

class Music:
    """A music class is a notes object populated from an on disk midi file.
        self.notes is a list of all the notes in the file for rendering and scoring
        self.keys is a dictionary keyed by note number to keep track on note on and note off events."""

    Accidentals = {1: True, 3: True, 6: True, 8: True, 10: True, 13: True, 15: True, 18: True, 20: True}

    def __init__(self, graphics: Graphics, font: Font, staff_pos: list, note_positions: list, filename: str):
        self.graphics = graphics
        self.mid = MidiFile(filename)
        self.clocks_per_tick = 24
        self.num_32nd_notes_per_beat = 8
        self.time_signature = (4,4)
        self.key_signature = KeySignature()
        self.font = font
        self.note_positions = note_positions
        self.notes = Notes(graphics, font, staff_pos, note_positions, Music.Accidentals)
        self.keys = {}
        absolute_time = 0
        for _, track in enumerate(self.mid.tracks):
            for msg in track:
                if isinstance(msg, MetaMessage):
                    if msg.type == 'time_signature':
                        self.time_signature = (msg.numerator, msg.denominator)
                        self.clocks_per_tick = msg.clocks_per_click
                        self.num_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                    elif msg.type == 'key_signature':
                        self.key_signature = KeySignature(msg.key)
                elif isinstance(msg, Message):
                    # note_on with velocity of 0 is interpreted as note_off
                    if msg.type == 'note_on' and msg.velocity > 0:
                        absolute_time += msg.time
                        self.keys[msg.note] = absolute_time
                    elif msg.type == 'note_off' or msg.type == 'note_on' and msg.velocity <= 0:
                        if msg.note in self.keys:
                            note_length = absolute_time + msg.time - self.keys[msg.note]
                            length_in_32s = math.ceil(note_length / self.clocks_per_tick)
                            time_in_32s = math.ceil(self.keys[msg.note] / self.clocks_per_tick)                        
                            
                            absolute_time += msg.time

                            self.notes.add(msg.note, time_in_32s, length_in_32s)
                            self.keys.pop(msg.note)

    def reset(self):
        """Restore all the notes in the music to the state just after loading."""

        self.notes.reset()

    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        # Draw the key signature translucent
        spacing = 0.076
        acc_size = 90
        acc_col = [0.33, 0.33, 0.33, 0.5]
        for i, acc in enumerate(self.key_signature.sharps):
            acc_pos = [i * spacing, self.note_positions[acc]]
            self.font.draw(Note.AccidentalCharacters[1], acc_size, acc_pos, acc_col)
        for i, acc in enumerate(self.key_signature.flats):
            acc_pos = [i * spacing, self.note_positions[acc]]
            self.font.draw(Note.AccidentalCharacters[-1], acc_size, acc_pos, acc_col)

        return self.notes.draw(dt, music_time, note_width)

class KeySignature:
    """A POD style class to keep store the params of music key in reference to the midi meta-message for key signature."""

    def __init__(self, key:str='C'):
        self.sharps = []
        self.flats = []
        self.major = key.find("m") < 0
        self.key = key

        def add_sharps_and_flats(table):
            for _, acc in enumerate(table):
                if acc[1:] == 'b':
                    self.flats.append(KeySignature.LookupTableKeyToIndex[acc[0:1]])
                elif acc[1:] == '#':
                    self.sharps.append(KeySignature.LookupTableKeyToIndex[acc[0:1]])

        tonic = key.replace('m', '')
        if self.major:
            add_sharps_and_flats(KeySignature.LookupTableMajor[tonic])
        else:
            add_sharps_and_flats(KeySignature.LookupTableMinor[tonic])
            
    def __str__(self):
        return self.key

    LookupTableKeyToIndex = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 6, 'A': 9, 'B': 11
    }

    LookupTableMajor = {
        'Cb': ['Cb', 'Db', 'Eb', 'Fb', 'Gb', 'Ab', 'Bb'], # 7 flats
        'Gb': ['Gb','Ab', 'Bb', 'Cb', 'Db',	'Eb'], # 6 flats
        'Db': ['Db', 'Eb', 'Gb', 'Ab', 'Bb'], # 5 flats
        'Ab': ['Ab', 'Bb', 'Db', 'Eb', ], # 4 flats
        'Eb': ['Eb', 'Ab', 'Bb',], # 3 flats
        'Bb': ['Bb', 'Eb',], # 2 flats
        'F': ['Bb'], # 1 flat
        'C': [], # no flats or sharps
        'G': ['F#'], # 1 sharp
        'D': ['F#', 'C#'], # 2 sharps
        'A': ['C#', 'F#', 'G#'], # 3 sharps
        'E': ['F#',	'G#', 'C#', 'D#'], # 4 sharps
        'B': ['C#',	'D#', 'F#', 'G#', 'A#'], # 5 sharps
        'F#': ['F#', 'G#','A#', 'C#','D#','E#'], # 6 sharps
        'C#': ['C#', 'D#', 'E#', 'F#', 'G#', 'A#', 'B#'], # 7 sharps
    }

    LookupTableMinor = {
        'Ab': ['Ab', 'Bb', 'Cb', 'Db', 'Eb', 'Fb', 'Gb'], # 7 flats
        'Eb': ['Eb', 'Gb', 'Ab', 'Bb', 'Cb', 'Db'], # 6 flats
        'Bb': ['Bb', 'Db', 'Eb', 'Gb', 'Ab'], # 5 flats
        'F': ['Ab', 'Bb', 'Db', 'Eb'], # 4 flats
        'C': ['Eb',	'Ab', 'Bb'], # 3 flats
        'G': ['Bb', 'Eb'], # 2 flats
        'D': ['Bb'], # 1 flat
        'A': [], # no flats or sharps
        'E': ['F#'], # 1 sharp
        'B': ['C#', 'F#'], # 2 sharps
        'F#': ['F#', 'G#', 'C#'], # 3 sharps
        'C#': ['C#', 'D#', 'F#', 'G#'], # 4 sharps
        'G#': ['G#', 'A#', 'C#', 'D#', 'F#'], # 5 sharps
        'D#': ['D#', 'E#', 'F#', 'G#', 'A#', 'C#'], # 6 sharps
        'A#': ['A#', 'B#', 'C#', 'D#', 'E#', 'F#', 'G#'], # 7 sharps
    }
