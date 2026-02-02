import os
import math
from mido import (
    MidiFile,
    Message, MetaMessage,
    tempo2bpm
)
import numpy.random as rng
from note import Note
from key_signature import KeySignature
from score import MAX_SCORE_PER_NOTE

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
        self.track_names: dict[str] = {}
        self.backing_tracks: dict[list[Message]] = {}
        self.notes: list[Note] = []
        self.saved = False
        self.dirty = False

    def get_name(self):
        return f"{self.artist} - {self.title}"

    def get_max_score(self):
        """Calculate maximum possible score for the song."""
        if not self.notes:
            return 1

        return len(self.notes) * 10

    @staticmethod
    def _get_notes_in_key(key: str, note_range: tuple = (48, 80)):
        """Get all MIDI note numbers within a key across the specified range.
        Args:
            key: Musical key (e.g., 'C', 'Gm' for G minor)
            note_range: Tuple of (min_note, max_note) MIDI note numbers
        Returns:
            List of MIDI note numbers that belong to the key
        """
        # Determine if major or minor
        is_major = key.find('m') < 0
        tonic = key.replace('m', '')
        
        # Get the sharps/flats for this key
        if is_major:
            accidentals = KeySignature.LookupTableMajor.get(tonic, [])
        else:
            accidentals = KeySignature.LookupTableMinor.get(tonic, [])

        # Build the scale using semitone pattern
        # Major: W-W-H-W-W-W-H (2-2-1-2-2-2-1)
        # Minor: W-H-W-W-H-W-W (2-1-2-2-1-2-2)
        semitone_pattern = [2, 2, 1, 2, 2, 2, 1] if is_major else [2, 1, 2, 2, 1, 2, 2]

        # Find the root note (C=0, C#=1, D=2, etc.)
        note_to_midi = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        root = note_to_midi.get(tonic[0], 0)

        # Adjust for sharps/flats in the tonic
        if len(tonic) > 1:
            if tonic[1] == '#':
                root = (root + 1) % 12
            elif tonic[1] == 'b':
                root = (root - 1) % 12

        # Build scale degrees in one octave
        scale_degrees = [root]
        current = root
        for interval in semitone_pattern[:-1]:  # Last interval wraps to octave
            current = (current + interval) % 12
            scale_degrees.append(current)

        # Generate all notes in the key within the range
        notes_in_key = []
        for midi_note in range(note_range[0], note_range[1]):
            if midi_note % 12 in scale_degrees:
                notes_in_key.append(midi_note)

        return notes_in_key

    def add_count_in(self, num_notes:int=4, note_length: int=32, note_spacing: int=32, note:int=80):
        time_in_32s = 0
        self.backing_tracks[0] = []
        for i in range(num_notes):
            click_on = Message("note_on")
            click_on.note = note
            click_on.velocity = 100
            click_on.time = i * note_spacing

            click_off = Message("note_on")
            click_off.note = note
            click_off.velocity = 100
            click_off.time = (i * note_spacing) + note_length
            self.backing_tracks[0].append(click_on)
            self.backing_tracks[0].append(click_off)
            time_in_32s += note_spacing

    def add_random_notes(self,
                         num_notes:int,
                         key:str="C",
                         tonic:int=60,
                         note_range:int=4,
                         note_length:int=32,
                         note_spacing:int=0,
                         time: int=0):
        """Add a sequence of random notes to the song.
        Args:
            num_notes: Number of notes to add
            key: Musical key (e.g., 'C', 'Gm'). If provided, only notes from this key will be used
            tonic: Center note to start generating from
            note_range: Number of notes above and below the tonic to generate from
            note_length: Length of each note in 32nd notes
            note_spacing: Spacing between notes in 32nd notes
            
        """
        allowed_notes = [tonic - note_range + n for n in range(note_range*2)]

        # Filter to only notes that are both in the key and in allowed_notes
        min_note = min(allowed_notes)
        max_note = max(allowed_notes) + 1
        notes_in_key = self._get_notes_in_key(key, (min_note, max_note))
        allowed_notes = [n for n in allowed_notes if n in notes_in_key]
        if not allowed_notes:
            raise ValueError(f"No notes in key '{key}' within the allowed note range")

        # Calculate starting time based on existing notes
        time_in_32s = 0
        if self.notes:
            last_note = self.notes[-1]
            time_in_32s = last_note.time + last_note.length
        time_in_32s += time

        for _ in range(num_notes):
            note_value = rng.choice(allowed_notes).item()
            self.notes.append(Note(note_value, time_in_32s, note_length))
            time_in_32s += note_length + note_spacing

    def from_random(self,
                    key:str="C",
                    tonic:int=60,
                    note_range:int=4,
                    note_len_range:tuple=(32, 32),
                    note_spacing_range:tuple=(32,32),
                    song_length_notes:int=16):
        """Generate a random song in a key.
        Args:
            key: Musical key (e.g., 'C', 'Gm'). If provided, only notes from this key will be used
            tonic: Center note to start generating from
            note_range: Number of notes above and below the tonic to generate from
            note_len_range: Tuple of (min, max) note lengths in 32nd notes
            note_spacing_range: Tuple of (min, max) spacing between notes in 32nd notes
            song_length_notes: Number of notes to generate
            
        """
        self.key_signature = key
        self.artist = f"Random"
        title_suffix = f" in {key}" if key else ""
        self.title = f"{song_length_notes} notes of {note_len_range[0]} to {note_len_range[1]} length{title_suffix}."
        self.path = ""
        self.ticks_per_beat = Song.SDQNotesPerBeat
        self.player_track_id = 0
        self.saved = False

        # Use add_random_notes for the core logic
        note_length = note_len_range[0] if note_len_range[0] == note_len_range[1] else rng.randint(note_len_range[0], note_len_range[1])
        spacing = note_spacing_range[0] if note_spacing_range[0] == note_spacing_range[1] else rng.randint(note_spacing_range[0], note_spacing_range[1])
        self.add_random_notes(song_length_notes, key, tonic, note_range, note_length, spacing)

    def from_midi_file(self, filepath: str, player_track_id: int = 0):
        keys = {}
        if not os.path.exists(filepath):
            return

        self.path = filepath
        self.saved = True

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
