from texture import *
from graphics import *
from font import *

class Note():
    """Note is a POD style container for a note in a piece of music with representation."""

    NoteCharacters = {
        32: "w",
        16: "h",
        8: "q",
        4: "e",
        2: "s",
        1: "s",
    }

    AccidentalCharacters = { 
        1: "B", 
        0: "½", 
        -1: "b" 
    }

    @staticmethod
    def get_quantized_length(note_length):
        for i, k in enumerate(Note.NoteCharacters):
            if note_length >= k:
                return k
        return 1

    def __init__(self, note: int, time: int, length: int):
        self.note = note
        self.time = time
        self.length = length

class NoteSprite():
    """NoteSprite is the visual representation of a note that is drawn with a font character. 
        It owns an index into the Notes class note array of note data for scoring and timing."""

    def __init__(self, font: Font):
        self.note_id = -1
        self.font = font

    def assign(self, note_id: int, note: int, time: int, length: int, pitch_pos: float, note_char: str, accidental=None):
        self.note = note
        self.time = time
        self.length = length
        self.pitch_pos = pitch_pos
        self.note_id = note_id
        self.note_char = note_char
        self.accidental = accidental

    def recycle(self):
        self.note_id = -1
        
    def draw(self, music_time: float, note_width: float, origin_note_x: int, notes_on: dict):
        if self.note_id >= 0:
            note_time_offset = 0.95 # Beat one of the bar starts after the barline
            note_pos = [origin_note_x - note_time_offset + ((self.time - music_time) * note_width), self.pitch_pos + 0.0125]
            note_col = [0.1, 0.1, 0.1, 1.0]
            
            if self.accidental is not None:
                self.font.draw(Note.AccidentalCharacters[self.accidental], 72, [note_pos[0] - 0.02, note_pos[1]], note_col)

            self.font.draw(self.note_char, 158, note_pos, note_col)
            
            if self.time <= music_time:
                notes_on[self.note] = music_time + self.length
                self.recycle()

class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen. There is a pool
    of onscreen notes that recycled when they reach the playhead."""
            
    def __init__(self, graphics:Graphics, font: Font, staff_pos: list, note_positions: list, accidentals: dict):
        self.notes = []
        self.graphics = graphics
        self.note_pool = []
        self.note_pool_offset = 0
        self.note_pool_size = 32
        self.notes_offset = 0
        self.prev_note = 0
        self.accidentals = accidentals
        self.note_positions = note_positions
        self.pos = staff_pos
        self.origin_note_pitch = 60 # Using C4 as reference note
        self.font = font
        self.origin_note_y = self.pos[1] - 0.33
        self.origin_note_x = staff_pos[0]
        self.notes_on = {}

        # Create the barlines with 0 being the immovable 0 bar
        self.num_barlines = 8
        self.barlines = []
        self.bartimes = []
        staff_width = 0.085 * 2 * 4
        for i in range(self.num_barlines):
            barline = SpriteShape(self.graphics, [0.0, 0.0, 0.0, 1.0], [0.0, 0.0], [0.011, staff_width])
            self.barlines.append(barline)
            self.bartimes.append(i * 32.0)
            
        # Fill the note pool with inactive note sprites to be assigned data when drawn
        for i in range(self.note_pool_size):
            self.note_pool.append(NoteSprite(self.font))

    def reset(self):
        """Restore the note pool and barlines to their original state."""
        
        for _, note in enumerate(self.note_pool):
            note.recycle()

        self.notes_offset = 0
        self.prev_note = 0
        for _, note in enumerate(self.notes):
            if self.note_pool_offset < self.note_pool_size - 1:
                self.assign_note()

        for i in range(self.num_barlines):
            self.bartimes[i] = i * 32.0

        self.notes_on = {}

    def add(self, pitch: int, time: int, length: int):
        self.notes.append(Note(pitch, time, length))

        # Automatically assign the first 32 notes that are added from the music
        if self.note_pool_offset < self.note_pool_size - 1:
            self.assign_note()

    def assign_note(self):
        # Search for an inactive note in the pool to assign to
        if self.note_pool[self.note_pool_offset].note_id >= 0:
            for i in range(len(self.note_pool)):
                if self.note_pool[i].note_id < 0:
                    self.note_pool_offset = i
                    break

        # This will evaluate true when there is a piece of music with 32 notes in 2 bars
        if self.note_pool[self.note_pool_offset].note_id >= 0:
            print("Failed to find an inactive note sprite in the pool!")

        if self.notes_offset < len(self.notes):
            note_sprite = self.note_pool[self.note_pool_offset]
            note = self.notes[self.notes_offset]

            # Handle accidentals, sharp going up, flat coming down
            note_lookup = note.note
            accidental = None
            if note.note % 12 in self.accidentals:
                melody_dir_up = self.prev_note < note_lookup
                if melody_dir_up:
                    accidental = 1
                    note_lookup -= 1
                else:
                    accidental = -1
                    note_lookup += 1
            self.prev_note = note_lookup

            note_diff = self.note_positions[note_lookup % 12]
            num_octaves = (note.note - 60) // 12
            per_octave = self.note_positions[12]
            pitch_diff = -note_diff - (num_octaves * per_octave)
            lead_in = 32
            note_time = lead_in + note.time

            quantized_length = Note.get_quantized_length(note.length)
            note_sprite.assign(self.notes_offset, note.note, note_time, note.length, self.origin_note_y - pitch_diff, Note.NoteCharacters[quantized_length], accidental)
            self.notes_offset += 1
            
    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """ Draw and update the bar lines and all notes in the pool.
        Return a dictionary keyed on note numbers with value of the end music time note length
        """

        # Draw a recycled list of barlines moving from right to left
        for i in range(self.num_barlines):
            bar_start = self.origin_note_x - 0.92
            self.barlines[i].pos[0] = bar_start + ((self.bartimes[i] - music_time) * note_width)
            self.barlines[i].pos[1] = self.pos[1] + 0.25
            self.barlines[i].draw()
            if self.bartimes[i] < music_time:   
                self.bartimes[i] += self.num_barlines * 32
                          
        # Draw all the notes in the pool
        for i in range(len(self.note_pool)):
            self.note_pool[i].draw(music_time, note_width, self.origin_note_x, self.notes_on)

        return self.notes_on
