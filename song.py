import os
import math
from mido import (
    MidiFile,
    Message, MetaMessage,
    tempo2bpm
)
import numpy.random as rng
from note import Note 

class Song:
    """A song is a combination of music notes and metadata that the game uses to 
    play and display each song. Player score and progress data is stored with the
    music alongside per-song options.
    """
    SDQNotesPerBeat = 8  # 32nd notes
    MinNoteLength32s = 2 # 16th note
    QuantizeTime32s = 2 # Snap to each 16th note
    MinVelocity = 64 # 50% of max

    def __init__(self):
        self.artist = "Unknown Artist"
        self.title = "Song"
        self.path = ""
        self.score = {}
        self.player_track_id = 0
        self.tempo_bpm = 60
        self.time_signature = (4, 4)
        self.key_signature = "C"
        self.clocks_per_tick = 24
        self.ticks_per_beat = Song.SDQNotesPerBeat
        self.track_names = {}
        self.backing_tracks = {}
        self.notes: list[Note] = []
        self.dirty = False


    def get_name(self):
        return f"{self.artist} - {self.title}"


    def get_max_score(self):
        return max(len(self.notes), 1) * 10


    def from_random(self, note_len_range: tuple, note_spacing_range: tuple, song_length_notes:int=16, allowed_notes:list=None):
        if allowed_notes is None:
            allowed_notes = [48 + n for n in range(32)]
        self.artist = f"Random"
        self.title = f"{song_length_notes} notes of {note_len_range[0]} to {note_len_range[1]} length."
        self.path = ""
        self.ticks_per_beat = Song.SDQNotesPerBeat
        self.player_track_id = 0
        time_in_32s = 0
        for _ in range(song_length_notes):
            length_in_32s = note_len_range[0] if note_len_range[0] == note_len_range[1] else rng.randint(note_len_range[0], note_len_range[1])
            note_value = rng.choice(allowed_notes)
            self.notes.append(Note(note_value, time_in_32s, length_in_32s))
            time_in_32s += note_spacing_range[0] if note_spacing_range[0] == note_spacing_range[1] else rng.randint(note_spacing_range[0], note_spacing_range[1])


    def from_midi_file(self, filepath: str, player_track_id: int = 0):
        keys = {}
        if not os.path.exists(filepath):
            return

        self.path = filepath

        # Derive track name from filename
        filestr = str(filepath)
        last_dir_sep = filestr.rfind(os.sep)
        lsep = filestr.rfind('/')
        wsep = filestr.rfind('\\')
        last_dir_sep = max(last_dir_sep, lsep, wsep)
        songname = filestr if last_dir_sep <= 0 else filestr[last_dir_sep + 1:]
        self.title = songname.replace('.mid', '')
        self.artist = "MidiFile"

        for sep in ['-', ':', "_"]:
            if self.title.find(sep) >= 0:
                song_name_elems = self.title.split(sep)
                self.artist = song_name_elems[0].strip()
                self.title = song_name_elems[1].strip()
                break

        mid = MidiFile(filepath)
        self.ticks_per_beat = mid.ticks_per_beat
        self.player_track_id = player_track_id
        absolute_time = 0
        for id, track in enumerate(mid.tracks):
            if track.name:
                self.track_names[id] = track.name
            for msg in track:
                if isinstance(msg, MetaMessage):
                    if msg.type == "set_tempo":
                        self.tempo_bpm = tempo2bpm(msg.tempo)
                    elif msg.type == "time_signature":
                        self.time_signature = (msg.numerator, msg.denominator)
                        self.clocks_per_tick = msg.clocks_per_click
                        self.num_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                    elif msg.type == "key_signature":
                        self.key_signature = msg.key
                    elif msg.type == "track_name":
                        self.track_names[id] = msg.name
                if id == player_track_id:
                    if isinstance(msg, Message):
                        # note_on with velocity of 0 is interpreted as note_off
                        if msg.type == "note_on" and msg.velocity >= Song.MinVelocity:
                            absolute_time += msg.time
                            keys[msg.note] = absolute_time
                        elif msg.type == "note_off" or msg.type == "note_on" and msg.velocity <= 0:
                            if msg.note in keys:
                                note_length = absolute_time + msg.time - keys[msg.note]
                                length_in_32s = math.ceil(note_length / self.ticks_per_beat * Song.SDQNotesPerBeat)
                                time_in_32s = math.ceil(keys[msg.note] / self.ticks_per_beat * Song.SDQNotesPerBeat)
                                if length_in_32s >= Song.MinNoteLength32s:
                                    self.notes.append(Note(msg.note, time_in_32s, length_in_32s))
                                    keys.pop(msg.note)
                                absolute_time += msg.time
                else:
                    if not isinstance(msg, MetaMessage):
                        if id in self.backing_tracks:
                            self.backing_tracks[id].append(msg)
                        else:
                            self.backing_tracks[id] = []
                            self.backing_tracks[id].append(msg)

        # Add a lead in if the first notes to be played start within a bar
        if len(self.notes) > 0:
            if self.notes[0].time < 32:
                lead_in_32s = 32
                for note in self.notes:
                    note.time += lead_in_32s
                for _, track in enumerate(self.backing_tracks):
                    for note in self.backing_tracks[track]:
                        note.time += lead_in_32s
