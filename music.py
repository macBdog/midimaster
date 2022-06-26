from mido import MidiFile
from mido import MetaMessage
from mido import Message
from mido import tempo2bpm
from midi_devices import MidiDevices
from notes import Notes
from graphics import Graphics
from note_render import NoteRender
from staff import Staff
import math


class Music:
    """A music class is a notes object populated from an on disk midi file.
    self.notes is a list of all the notes in the file for rendering and scoring
    self.keys is a dictionary keyed by note number to keep track on note on and note off events."""

    SDQNotesPerBeat = 8  # 32nd notes

    def __init__(self, graphics: Graphics, note_render: NoteRender, staff: Staff, filename: str, track_id: int = 0):
        self.graphics = graphics
        self.mid = MidiFile(filename)
        self.clocks_per_tick = 24
        self.ticks_per_beat = self.mid.ticks_per_beat
        self.time_signature = (4, 4)
        self.tempo_bpm = 120.0
        self.staff = staff
        self.note_positions = staff.get_note_positions()
        self.notes = Notes(graphics, note_render, staff, self.note_positions)
        self.keys = {}
        self.track_names = {}
        self.backing_tracks = {}
        self.backing_index = {}
        self.backing_time = {}

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
                        self.staff.key_signature.set(msg.key, self.note_positions)
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
                        if id in self.backing_tracks:
                            self.backing_tracks[id].append(msg)
                        else:
                            self.backing_tracks[id] = []
                            self.backing_index[id] = 0
                            self.backing_time[id] = 0.0
                            self.backing_tracks[id].append(msg)

        # Add a lead in if the first notes to be played start within a bar
        if self.notes.notes[0].time < 32:
            lead_in_32s = 32
            for note in self.notes.notes:
                note.time += lead_in_32s
            for _, track in enumerate(self.backing_tracks):
                for note in self.backing_tracks[track]:
                    note.time += lead_in_32s

        # Post-process the notes of the music, adding rests and decoration
        self.notes.assign_notes()

    def reset(self):
        """Restore all the notes in the music to the state just after loading."""

        self.notes.reset()
        self.backing_index = {track: 0 for track in self.backing_index}
        self.backing_time = {track: 0.0 for track in self.backing_time}
        
        
    def update(self, dt: float, music_time: float, devices: MidiDevices):
        """Play MIDI messages that are not for interactive scoring by the player."""

        music_time_in_ticks = (music_time / Music.SDQNotesPerBeat) * self.ticks_per_beat

        def update_backing_track(id: int, ticks_time: float):
            b_len = len(self.backing_tracks[id])
            b_index = self.backing_index[id]
            b_time = self.backing_time[id]
            if b_len == 0 or b_index >= b_len:
                return

            next_event = self.backing_tracks[id][b_index]
            while b_time <= ticks_time:
                if devices.output_port:
                    devices.output_port.send(next_event)
                self.backing_index[id] += 1
                b_index = self.backing_index[id]
                if b_index >= b_len:
                    break
                next_event = self.backing_tracks[id][b_index]
                self.backing_time[id] += next_event.time
                b_time = self.backing_time[id]

        for _, id in enumerate(self.backing_tracks):
            update_backing_track(id, music_time_in_ticks)

    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """Draw any parts of the scene that involve musical notation."""

        return self.notes.draw(dt, music_time, note_width)
