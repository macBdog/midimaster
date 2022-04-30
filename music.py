from mido import MidiFile
from mido import MetaMessage
from mido import Message
from mido import tempo2bpm
from midi_devices import MidiDevices
from notes import Notes
from font import Font
from graphics import Graphics
from texture import TextureManager
from gui import Gui
from key_signature import KeySignature
from staff import Staff
import math


class Music:
    """A music class is a notes object populated from an on disk midi file.
    self.notes is a list of all the notes in the file for rendering and scoring
    self.keys is a dictionary keyed by note number to keep track on note on and note off events."""

    SDQNotesPerBeat = 8  # 32nd notes

    def __init__(self, graphics: Graphics, font: Font, staff: Staff, note_positions: list, filename: str, track_id: int = 0):
        self.graphics = graphics
        self.mid = MidiFile(filename)
        self.clocks_per_tick = 24
        self.ticks_per_beat = self.mid.ticks_per_beat
        self.time_signature = (4, 4)
        self.tempo_bpm = 120.0
        self.key_signature = KeySignature()
        self.font = font
        self.staff = staff
        self.note_positions = note_positions
        self.notes = Notes(graphics, font, staff, note_positions, self.key_signature)
        self.keys = {}
        self.track_names = {}
        self.backing_track = []
        self.backing_index = 0
        self.backing_time = 0

        absolute_time = 0
        for id, track in enumerate(self.mid.tracks):
            for msg in track:
                if isinstance(msg, MetaMessage):
                    if msg.type == "set_tempo":
                        self.tempo_bpm = tempo2bpm(msg.tempo)
                    elif msg.type == "time_signature":
                        self.time_signature = (msg.numerator, msg.denominator)
                        self.clocks_per_tick = msg.clocks_per_click
                        self.num_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                    elif msg.type == "key_signature":
                        self.key_signature.set(msg.key)
                    elif msg.type == "track_name":
                        self.track_names[id] = msg.name
                if id == track_id:
                    if isinstance(msg, Message):
                        # note_on with velocity of 0 is interpreted as note_off
                        if msg.type == "note_on" and msg.velocity > 0:
                            absolute_time += msg.time
                            self.keys[msg.note] = absolute_time
                        elif msg.type == "note_off" or msg.type == "note_on" and msg.velocity <= 0:
                            if msg.note in self.keys:
                                note_length = absolute_time + msg.time - self.keys[msg.note]
                                length_in_32s = math.ceil(note_length / self.ticks_per_beat * Music.SDQNotesPerBeat)
                                time_in_32s = math.ceil(self.keys[msg.note] / self.ticks_per_beat * Music.SDQNotesPerBeat)
                                self.notes.add(msg.note, time_in_32s, length_in_32s)
                                self.keys.pop(msg.note)
                                absolute_time += msg.time
                else:
                    if not isinstance(msg, MetaMessage):
                        self.backing_track.append(msg)

        self.notes.add_rests()

    def reset(self):
        """Restore all the notes in the music to the state just after loading."""

        self.notes.reset()
        self.backing_index = 0
        self.backing_time = 0.0

    def update(self, dt: float, music_time: float, devices: MidiDevices):
        """Play MIDI messages that are not for interactive scoring by the player."""

        backing_track_len = len(self.backing_track)
        if backing_track_len == 0:
            return

        music_time_in_ticks = (music_time / Music.SDQNotesPerBeat) * self.ticks_per_beat
        next_event = self.backing_track[self.backing_index]
        while self.backing_time <= music_time_in_ticks:
            devices.output_port.send(next_event)
            self.backing_index += 1
            if self.backing_index >= backing_track_len:
                break
            next_event = self.backing_track[self.backing_index]
            self.backing_time += next_event.time

    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """Draw any parts of the scene that involve musical notation."""

        self.key_signature.draw(self.font, self.staff, self.note_positions)
        return self.notes.draw(dt, music_time, note_width)
