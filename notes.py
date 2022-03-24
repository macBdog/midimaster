from texture import *
from graphics import *
from font import *

class Note():
    """Note is a POD style container for a note in a piece of music with representation."""
    def __init__(self, note: int, time: int, length: int):
        self.note = note
        self.time = time
        self.length = length

class NoteSprite():
    """NoteSprite is the visual representation of a note that is drawn with a font character. 
        It owns an index into the Notes class note array of note data for scoring and timing.
    """
    def __init__(self, font: Font):
        self.note_id = -1
        self.font = font

    def assign(self, note_id: int, note: int, time: int, length: int, pitch_pos: float, note_char: str):
        self.note = note
        self.time = time
        self.length = length
        self.pitch_pos = pitch_pos
        self.note_id = note_id
        self.note_char = note_char

    def recycle(self):
        self.note_id = -1
        
    def draw(self, music_time: float, note_width: float, origin_note_x: int, notes_on: dict):
        if self.note_id >= 0:
            note_time_offset = 0.80 # Beat one of the bar starts after the barline
            self.font.draw(self.note_char, 158, [origin_note_x - note_time_offset + ((self.time - music_time) * note_width), self.pitch_pos + 0.0125], [0.1, 0.1, 0.1, 1.0])
            if self.time <= music_time:
                notes_on[self.note] = music_time + self.length
                self.recycle()

class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen. There is a pool
    of onscreen notes that recycled when they reach the playhead.
    """
    def __init__(self, graphics:Graphics, textures: TextureManager, font: Font, staff_pos: list, note_positions: list, incidentals: dict):
        self.notes = []
        self.graphics = graphics
        self.note_pool = []
        self.note_pool_offset = 0
        self.note_pool_size = 32
        self.notes_offset = 0
        self.incidentals = incidentals
        self.note_positions = note_positions
        self.pos = staff_pos
        self.origin_note_pitch = 60 # Using middle C4 as the reference note
        self.font = font
        self.origin_note_y = -0.33 #self.pos[1] - 0.15
        self.origin_note_x = staff_pos[0]
        self.note_characters = {}
        self.notes_on = {}
        self.add_note_definition(32, "w")
        self.add_note_definition(16, "h")
        self.add_note_definition(8, "q")
        self.add_note_definition(4, "e")
        self.add_note_definition(2, "s")
        self.add_note_definition(1, "s")

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

    def add_note_definition(self, num_32nd_notes: int, font_character: str):
        self.note_characters.update({num_32nd_notes: font_character})

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

            note_diff = self.note_positions[note.note % 12]
            num_octaves = (note.note - 60) // 12
            per_octave = self.note_positions[12]
            pitch_diff = -note_diff - (num_octaves * per_octave)
            lead_in = 32
            note_time = lead_in + note.time
            
            if note.length in self.note_characters:
                note_sprite.assign(self.notes_offset, note.note, note_time, note.length, self.origin_note_y - pitch_diff, self.note_characters[note.length])
            elif GameSettings.dev_mode:
                print(f"Ignoring invalid note of length {note.length}")
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
