from texture import *
from graphics import *
from font import *
from key_signature import KeySignature
from staff import Staff

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
    RestCharacters = {
        32: "W",
        16: "H",
        8: "Q",
        4: "E",
        2: "S",
        1: "S",     
    }
    DottedChar = '.'

    @staticmethod
    def get_quantized_length(note_length):
        for i, k in enumerate(Note.NoteCharacters):
            if note_length >= k:
                remainder = note_length - k
                dotted = remainder >= k / 2
                return k, dotted
        return 1, False

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

    def assign(self, note_id: int, note: int, time: int, length: int, pitch_pos: float, note_char: str, accidental, dotted):
        self.note = note
        self.time = time
        self.length = length
        self.pitch_pos = pitch_pos
        self.note_id = note_id
        self.note_char = note_char
        self.accidental = accidental
        self.dotted = dotted

    def recycle(self):
        self.note_id = -1
        
    def draw(self, music_time: float, note_width: float, origin_note_x: int, notes_on: dict):
        """Draw a note and it's associated accents, accidentals and dots.
        :return True if the note can be reassigned after drawning.
        """
        if self.note_id >= 0:
            if self.time - music_time < 32 * 4:
                note_time_offset = 0.95 # Beat one of the bar starts after the barline
                note_pos = [origin_note_x - note_time_offset + ((self.time - music_time) * note_width), self.pitch_pos + 0.0125]
                note_col = [0.1, 0.1, 0.1, 1.0]
                
                if self.accidental is not None:
                    self.font.draw(self.accidental, 72, [note_pos[0] - 0.02, note_pos[1]], note_col)

                if self.dotted:
                    self.font.draw(Note.DottedChar, 72, [note_pos[0] + 0.12, note_pos[1] + 0.035], note_col)

                self.font.draw(self.note_char, 158, note_pos, note_col)
                
                if self.time <= music_time:
                    notes_on[self.note] = music_time + self.length
                    self.recycle()

        return self.note_id >= 0
class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen. There is a pool
    of onscreen notes that recycled when they reach the playhead.
    """    
    def __init__(self, graphics:Graphics, font: Font, staff: Staff, note_positions: list, key_signature: KeySignature):
        self.notes = []
        self.rests = []
        self.graphics = graphics

        self.note_pool = []
        self.note_pool_offset = 0
        self.note_pool_size = 32
        self.notes_offset = 0

        self.rest_pool = []
        self.rest_pool_offset = 0
        self.rest_pool_size = 32
        self.rests_offset = 0

        self.prev_note = 0
        self.key_signature = key_signature
        self.note_positions = note_positions
        self.staff = staff
        self.font = font
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
            
        # Fill the note and rest pools with inactive note sprites to be assigned data when drawn
        for i in range(self.note_pool_size):
            self.note_pool.append(NoteSprite(self.font))
        for i in range(self.rest_pool_size):
            self.rest_pool.append(NoteSprite(self.font))

    def reset(self):
        """Restore the note pool and barlines to their original state."""
        
        for _, note in enumerate(self.note_pool):
            note.recycle()

        for _, rest in enumerate(self.rest_pool):
            rest.recycle()

        self.notes_offset = 0
        self.rests_offset = 0
        self.prev_note = 0
        for _, note in enumerate(self.notes):
            if self.note_pool_offset < self.note_pool_size - 1:
                self.assign_note()

        for _, rest in enumerate(self.rests):
            if self.rest_pool_offset < self.rest_pool_size - 1:
                self.assign_rest()

        for i in range(self.num_barlines):
            self.bartimes[i] = i * 32.0

        self.notes_on = {}

    def add(self, pitch: int, time: int, length: int):
        self.notes.append(Note(pitch, time, length))

        # Automatically assign the first 32 notes that are added from the music
        if self.note_pool_offset < self.note_pool_size - 1:
            self.assign_note()
    
    def add_rests(self):
        """Walk through each note in the music looking for spaces between notes to insert rests."""

        self.rests = []
        note_count = 0
        while note_count < len(self.notes) - 1:
            note = self.notes[note_count]
            next_note = self.notes[note_count + 1]
            rest_start = note.time + note.length
            rest_length = next_note.time - rest_start
            if rest_length > 0:
                self.rests.append(Note(0, rest_start, rest_length))
                if self.rest_pool_offset < self.rest_pool_size - 1:
                    self.assign_rest()
            note_count += 1

    def assign_rest(self):
        """Search for an inactive rest in the pool to assign the current rests_offset to"""

        if self.rest_pool[self.rest_pool_offset].note_id >= 0:
            for i in range(len(self.note_pool)):
                if self.rest_pool[i].note_id < 0:
                    self.rest_pool_offset = i
                    break

        # This will evaluate true when there is a piece of music with 32 rests
        if self.rest_pool[self.rest_pool_offset].note_id >= 0:
            return

        if self.rests_offset < len(self.rests):
            rest_sprite = self.rest_pool[self.note_pool_offset]
            rest = self.rests[self.rests_offset]
        
            quantized_length, dotted = Note.get_quantized_length(rest.length)
            rest_sprite.assign(self.rests_offset, rest.note, rest.time, rest.length, self.staff.pos[1], Note.RestCharacters[quantized_length], None, dotted)
            self.rests_offset += 1
                
    def assign_note(self):
        """Search for an inactive note in the pool to assign the current notes_offset to"""

        if self.note_pool[self.note_pool_offset].note_id >= 0:
            for i in range(len(self.note_pool)):
                if self.note_pool[i].note_id < 0:
                    self.note_pool_offset = i
                    break

        # This will evaluate true when there is a piece of music with 32 notes
        if self.note_pool[self.note_pool_offset].note_id >= 0:
            return

        if self.notes_offset < len(self.notes):
            note_sprite = self.note_pool[self.note_pool_offset]
            note = self.notes[self.notes_offset]

            # Handle accidentals, sharp going up, flat coming down
            note_lookup, accidental = self.key_signature.get_accidental(note.note, self.prev_note, [])
            self.prev_note = note_lookup

            note_diff = self.note_positions[note_lookup % 12]
            num_octaves = (note.note - self.staff.ref_note) // 12
            per_octave = self.note_positions[12]
            pitch_diff = -note_diff - (num_octaves * per_octave)

            quantized_length, dotted = Note.get_quantized_length(note.length)
            note_sprite.assign(self.notes_offset, note.note, note.time, note.length, self.staff.ref_note_pos[1] - pitch_diff, Note.NoteCharacters[quantized_length], accidental, dotted)
            self.notes_offset += 1
            
    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """ Draw and update the bar lines and all notes in the pool.
        Return a dictionary keyed on note numbers with value of the end music time note length."""

        # Draw a recycled list of barlines moving from right to left
        for i in range(self.num_barlines):
            bar_start = self.staff.ref_note_pos[0] - 0.92
            rel_time = self.bartimes[i] - music_time
            self.barlines[i].pos[0] = bar_start + (rel_time * note_width)
            self.barlines[i].pos[1] = self.staff.pos[1] + 0.25           
            
            if rel_time > 6:
                self.barlines[i].draw()

            if self.bartimes[i] < music_time:   
                self.bartimes[i] += self.num_barlines * 32
                          
        # Draw all the notes then rests in the pools
        free_note_index = -1
        for i in range(len(self.note_pool)):
            if self.note_pool[i].draw(music_time, note_width, self.staff.ref_note_pos[0], self.notes_on):
                free_note_index = i
        
        if free_note_index >= 0:
            self.assign_note()

        free_rest_index = -1
        for i in range(len(self.rest_pool)):
            if self.rest_pool[i].draw(music_time, note_width, self.staff.ref_note_pos[0], {}):
                free_rest_index = i

        if free_rest_index >= 0:
            self.assign_rest()

        return self.notes_on
