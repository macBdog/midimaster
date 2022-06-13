from texture import *
from graphics import *
from font import *
from staff import Staff
from note import Note
from note_render import NoteRender


class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen. There is a pool
    of onscreen notes that recycled when they reach the playhead.
    """    
    def __init__(self, graphics:Graphics, note_render: NoteRender, staff: Staff, note_positions: list):
        self.graphics = graphics
        self.note_render = note_render
        self.notes = []
        self.rests = []
        self.notes_offset = 0
        self.rests_offset = 0

        self.prev_note = 0
        self.note_positions = note_positions
        self.staff = staff
        self.ref_c4_pos = [Staff.Pos[0], note_positions[60]]
        self.notes_on = {}

        # Create the barlines with 0 being the immovable 0 bar
        self.num_barlines = 8
        self.barlines = []
        self.bartimes = []
        staff_width = Staff.StaffSpacing * 4.0
        for i in range(self.num_barlines):
            barline = SpriteShape(self.graphics, [0.0, 0.0, 0.0, 1.0], [0.0, 0.0], [0.008, staff_width])
            self.barlines.append(barline)
            self.bartimes.append(i * 32.0)

    def reset(self):
        """Restore the note pool and barlines to their original state."""
        
        self.notes_offset = 0
        self.rests_offset = 0
        self.prev_note = 0
        for _, note in enumerate(self.notes):
            self.assign_note()

        for _, rest in enumerate(self.rests):
            self.assign_rest()

        for i in range(self.num_barlines):
            self.bartimes[i] = i * 32.0

        self.notes_on = {}


    def add(self, pitch: int, time: int, length: int):
        # Don't display notes that cannot be played
        if pitch in self.note_positions:
            self.notes.append(Note(pitch, time, length))
        elif GameSettings.DEV_MODE:
            print(f"Ignoring a note that is out of playable range: {pitch}") 

        # Automatically assign all the notes in the music
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
                self.assign_rest()
            note_count += 1


    def assign_rest(self):
        """Get the next rest in the list and add it to the render as a note type"""

        if self.rests_offset < len(self.rests):
            rest = self.rests[self.rests_offset]
        
            quantized_length, dotted = Note.get_quantized_length(rest.length)
            
            self.rests_offset += 1
    

    def assign_note(self):
        """Get the next note in the list and add it to the render"""

        if self.notes_offset < len(self.notes):
            note = self.notes[self.notes_offset]

            # Handle accidentals, sharp going up, flat coming down
            note_lookup, accidental = self.staff.key_signature.get_accidental(note.note, self.prev_note, [])
            self.prev_note = note_lookup

            note_width_32 = 0.025 
            note_pos_x = self.ref_c4_pos[0] + (note.time * note_width_32)
            note_pos_y = self.note_positions[note_lookup]
            quantized_length, dotted = Note.get_quantized_length(note.length)

            pos = [note_pos_x, note_pos_y]
            type = Note.NoteLengthTypes[quantized_length]
            decoration = 1 if dotted else 0
            tail = [4.0, 0.0]
            tie = 0.0
            self.note_render.assign(note, pos, type, decoration, tail, tie)
            self.notes_offset += 1
        

    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """ Draw and update the bar lines and all notes on the GPU.
        Return a dictionary keyed on note numbers with value of the end music time note length."""

        # Draw a recycled list of barlines moving from right to left
        for i in range(self.num_barlines):
            bar_start = self.ref_c4_pos[0]
            rel_time = self.bartimes[i] - music_time
            self.barlines[i].pos[0] = bar_start + (rel_time * note_width)
            self.barlines[i].pos[1] = Staff.Pos[1] + Staff.StaffSpacing * 2.0           
            
            self.barlines[i].draw()

            if self.bartimes[i] < music_time:   
                self.bartimes[i] += self.num_barlines * 32
                          
        # Draw all the notes and return times for the ones that are playing
        self.note_render.draw(dt, music_time, note_width, self.notes_on)

        return self.notes_on
