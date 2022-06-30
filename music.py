
from gamejam.graphics import Graphics

from midi_devices import MidiDevices
from notes import Notes
from note_render import NoteRender
from staff import Staff
from song import Song


class Music:
    """A music class is a notes object populated from an on disk midi file.
    self.notes is a list of all the notes in the file for rendering and scoring
    self.keys is a dictionary keyed by note number to keep track on note on and note off events."""

    def __init__(self, graphics: Graphics, note_render: NoteRender, staff: Staff):
        self.graphics = graphics
        self.staff = staff
        self.note_positions = staff.get_note_positions()
        self.notes = Notes(graphics, note_render, staff, self.note_positions)
        self.song = None
        self.tempo_bpm = 60
        self.ticks_per_beat = Song.SDQNotesPerBeat
        self.backing_index = {}
        self.backing_time = {}


    def load(self, song:Song):
        """ Post-process the raw note data of the music, adding rests and decoration"""
        self.song = song
        self.tempo_bpm = song.tempo_bpm
        self.ticks_per_beat = song.ticks_per_beat

        for id in self.song.backing_tracks:
            self.backing_index[id] = 0
            self.backing_time[id] = 0.0

        self.staff.key_signature.set(song.key_signature, self.note_positions)
        self.notes.assign_notes(song.notes)


    def reset(self):
        """Restore all the notes in the music to the state just after loading."""
        self.notes.reset()
        self.backing_index = {track: 0 for track in self.backing_index}
        self.backing_time = {track: 0.0 for track in self.backing_time}
        
        
    def update(self, dt: float, music_time: float, devices: MidiDevices):
        """Play MIDI messages that are not for interactive scoring by the player."""
        music_time_in_ticks = (music_time / Song.SDQNotesPerBeat) * self.ticks_per_beat

        def update_backing_track(id: int, ticks_time: float):
            b_len = len(self.song.backing_tracks[id])
            b_index = self.backing_index[id]
            b_time = self.backing_time[id]
            if b_len == 0 or b_index >= b_len:
                return

            next_event = self.song.backing_tracks[id][b_index]
            while b_time <= ticks_time:
                if devices.output_port:
                    devices.output_port.send(next_event)
                self.backing_index[id] += 1
                b_index = self.backing_index[id]
                if b_index >= b_len:
                    break
                next_event = self.song.backing_tracks[id][b_index]
                self.backing_time[id] += next_event.time
                b_time = self.backing_time[id]

        for _, id in enumerate(self.song.backing_tracks):
            update_backing_track(id, music_time_in_ticks)


    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """Draw any parts of the scene that involve musical notation."""
        return self.notes.draw(dt, music_time, note_width)
