from mido import MidiFile
from mido import MetaMessage
from mido import Message
from notes import Note
from notes import Notes
import math

class Music:
    """A music class is a notes object populated from an on disk midi file.
        self.notes is a list of all the notes in the file for rendering and scoring
        self.keys is a dictionary keyed by note number to keep track on note on and note off events.
    """

    def __init__(self, screen, textures, staff_pos, filename: str):
        self.screen = screen
        self.textures = textures
        self.mid = MidiFile(filename)
        self.clocks_per_tick = 24
        self.num_32nd_notes_per_beat = 8
        self.time_signature = (4,4)
        self.tempo = 100
        self.notes = Notes(screen, textures, staff_pos, self.tempo)
        self.keys = {}
        accumulated_time = 0
        for i, track in enumerate(self.mid.tracks):
            for msg in track:
                if isinstance(msg, MetaMessage):
                    if msg.type == 'time_signature':
                        self.time_signature = (msg.numerator, msg.denominator)
                        self.clocks_per_tick = msg.clocks_per_click
                        self.num_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                elif isinstance(msg, Message):
                    print(msg)
                    last_event_time = msg.time
                    if msg.type == 'note_on':
                        self.keys[msg.note] = msg.time
                    elif msg.type == 'note_off':
                        if msg.note in self.keys:
                            absolute_time = accumulated_time + self.keys[msg.note]
                            accumulated_time += msg.time
                            time_in_32s = math.ceil(absolute_time / self.clocks_per_tick)
                            num_32nd_notes = math.ceil(msg.time / self.clocks_per_tick)
                            self.notes.add(msg.note, time_in_32s, num_32nd_notes)
                            self.keys.pop(msg.note)

        print("Notes parsed.")

    def draw(self, dt: float):
        self.notes.draw(dt)


