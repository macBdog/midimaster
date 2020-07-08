from mido import MidiFile
from mido import MetaMessage
from mido import Message
from notes import Note
from notes import Notes
from graphics import Graphics
from texture import TextureManager
import math

class Music:
    """A music class is a notes object populated from an on disk midi file.
        self.notes is a list of all the notes in the file for rendering and scoring
        self.keys is a dictionary keyed by note number to keep track on note on and note off events.
    """
    def __init__(self, graphics: Graphics, textures: TextureManager, staff_pos, note_positions: list, incidentals: dict, filename: str):
        self.graphics = graphics
        self.textures = textures
        self.mid = MidiFile(filename)
        self.clocks_per_tick = 24
        self.num_32nd_notes_per_beat = 8
        self.time_signature = (4,4)
        self.notes = Notes(graphics, textures, staff_pos, note_positions, incidentals)
        self.keys = {}
        absolute_time = 0
        last_note_off_time = 0
        rest_time = 0
        for i, track in enumerate(self.mid.tracks):
            for msg in track:
                if isinstance(msg, MetaMessage):
                    if msg.type == 'time_signature':
                        self.time_signature = (msg.numerator, msg.denominator)
                        self.clocks_per_tick = msg.clocks_per_click
                        self.num_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
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

    def draw(self, dt: float) -> dict:
        return self.notes.draw(dt)


