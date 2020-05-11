from mido import MidiFile
from mido import MetaMessage
from mido import Message
from notes import Note
from notes import Notes

class Music:
    """A music class is a notes object populated from an on disk midi file.
    """

    def __init__(self, screen, textures, staff_pos, filename: str):
        self.screen = screen
        self.textures = textures
        self.mid = MidiFile(filename)
        self.tempo = 120
        self.time_signature = (4,4)
        self.notes = Notes(screen, textures, staff_pos, self.tempo)

        for i, track in enumerate(self.mid.tracks):
            for msg in track:
                if isinstance(msg, MetaMessage):
                    if msg.type == 'time_signature':
                        self.time_signature = (msg.numerator, msg.denominator)
                        self.tempo = msg.clocks_per_click // msg.notated_32nd_notes_per_beat
                elif isinstance(msg, Message):
                    if msg.type == 'note_on':
                        self.notes.add(msg.note, msg.time)

    def draw(self, dt: float):
        self.notes.draw(dt)


