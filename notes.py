from texture import *
from graphics import *
from font import *
from staff import Staff
from note import Note, NoteType, NoteDecoration
from note_render import NoteRender


class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music, then notes manages when they should be on-screen.
    """    
    def __init__(self, graphics:Graphics, note_render: NoteRender, staff: Staff, note_positions: list):
        self.graphics = graphics
        self.note_render = note_render
        self.notes = []
        self.num_barlines = 8
        self.barlines = []
        self.bartimes = []

        self.note_positions = note_positions
        self.staff = staff
        self.ref_c4_pos = [Staff.Pos[0], note_positions[60]]
        
        # Create the barlines with 0 being the immovable 0 bar
        staff_width = Staff.StaffSpacing * 4.0
        for i in range(self.num_barlines):
            barline = SpriteShape(self.graphics, [0.0, 0.0, 0.0, 1.0], [0.0, 0.0], [0.008, staff_width])
            self.barlines.append(barline)
            self.bartimes.append(i * 32.0)
        
        self.reset()


    def reset(self):
        """Restore the note pool and barlines to their original state without clearing the music."""
        
        self.notes_offset = 0
        self.notes_on = {}

        for i in range(self.num_barlines):
            self.bartimes[i] = i * 32.0

        self.add_notes_to_render()


    def assign_notes(self):
        """Walk in sequence through the notes setting the decoration values for drawing."""

        note_id = 0
        time = 0
        bar_time_max = 32 # TODO Derive number of 32s in a bar from time signature
        bar_time = bar_time_max
        num_notes = len(self.notes)
        hats = []
        hat_max = 4
        prev_note = None
        prev_note_lookup = None

        def get_note_pos(time, pitch):
            return [time, self.note_positions[pitch]]

        while note_id < num_notes:
            note = self.notes[note_id]

            time_to_next = note.time - time

            # Handle rests greater than a bar
            if time_to_next >= bar_time_max:
                rest = Note(0, time + (bar_time_max // 2), bar_time_max)
                rest.decorate_rest(get_note_pos(time + (bar_time_max // 2), 64), Note.get_rest_type(bar_time_max))
                self.notes.insert(note_id, rest)
                time += bar_time_max
                note_id += 1
                num_notes += 1
                continue

            # Insert rests before the next note
            num_inserted_rests = 0
            while time_to_next > 0:
                rest_length = Note.get_quanitized_rest(time_to_next)
                rest = Note(0, time + (rest_length // 2), rest_length)
                rest.decorate_rest(get_note_pos(time + (rest_length // 2), 64), Note.get_rest_type(rest_length))
                self.notes.insert(note_id + num_inserted_rests, rest)
                time_to_next -= rest_length
                time += rest_length
                bar_time -= rest_length
                num_inserted_rests += 1

            # Advance to the next real note
            if num_inserted_rests > 0:
                note_id += num_inserted_rests
                num_notes += num_inserted_rests
                continue

            # Handle accidentals, sharp going up, flat coming down
            prev_note_lookup = prev_note.note % 12 if prev_note is not None else note.note % 12
            note.note_drawn, accidental = self.staff.key_signature.get_accidental(note.note, prev_note_lookup, [])
            quantized_length, dotted = Note.get_quantized_length(note.length)

            # Set timing type and dotted
            type = Note.get_note_type(quantized_length)
            decoration = NoteDecoration.DOTTED if dotted else NoteDecoration.NONE
            if accidental is not None:
                decoration = int(decoration.value) + 2 + accidental
                decoration = NoteDecoration(decoration)

            # Add hats only when we get to the end of the hat chain
            hat_num = len(hats)
            def add_all_hats(hats):
                hat_dir = 0.0
                hat_height = 0
                num_hats = len(hats)

                # Find the tallest note stem
                for h in hats:
                    if hat_dir >= 0.0:
                        if h.note_drawn > hat_height:
                            hat_height = h.note_drawn
                    elif h.note_drawn < hat_height:
                        hat_height = h.note_drawn
                
                if num_hats == 2:
                    y_diff = hats[0].note_drawn - hats[1].note_drawn
                    hats[0].hat = [hat_note.length, y_diff]
                    hats[1].hat = [0.0, 0.0]
                else:
                    for count in range(num_hats):
                        hat_note = hats[count]
                        hat_note.hat = [hat_note.length, 0.0]
                        hat_note.extra = [0.0, hat_height - hat_note.note_drawn]

                # Remove the tail from the last note in the chain
                hats[num_hats - 1].hat = [0.0, -1.0]

            if note.length <= 8:
                if hat_num < hat_max:
                    if hat_num == 0:
                        hats.append(note)
                    else:
                        if hats[hat_num - 1].length == note.length:
                            hats.append(note)
                        else:
                            add_all_hats()
                            hats = []
                            hats.append(note)
                
                # 4 notes max in one hat chain
                if len(hats) >= hat_max:
                    add_all_hats(hats)
                    hats = []
            elif hat_num > 0:
                add_all_hats(hats)
                hats = []
                            
            note.decorate(get_note_pos(note.time, note.note_drawn), type, decoration, note.hat, note.tie, note.extra)

            bar_time -= note.length
            time += note.length
            note_id += 1
            prev_note = note

        self.add_notes_to_render()
 
    def add_notes_to_render(self, num_notes:int=-1):
        # Add a number of notes to the render queue, -1 meaning add all."""
        # TODO: Right now we are adding the max notes on load, this will have to be replaced with a ring buffer style update during rendering

        notes_len = len(self.notes)
        num_to_add = num_notes if num_notes > 0 else notes_len - self.notes_offset
        for count in range(num_to_add):
            note = self.notes[count]
            self.note_render.assign(note)
            if GameSettings.DEV_MODE and not note.is_decorated():
                print(f"Error: Undecorated note added to note rendering!")

        self.notes_offset += num_to_add


    def add(self, pitch: int, time: int, length: int):
        # Don't display notes that cannot be played
        if pitch in self.note_positions:
            self.notes.append(Note(pitch, time, length))
        elif GameSettings.DEV_MODE:
            print(f"Ignoring a note that is out of playable range: {pitch}") 
    
    
    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """Draw and update the bar lines and all notes on the GPU.
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
