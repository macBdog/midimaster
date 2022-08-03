from copy import deepcopy

from gamejam.texture import SpriteShape
from gamejam.graphics import Graphics
from gamejam.settings import GameSettings

from staff import Staff
from note import Note, NoteDecoration
from note_render import NoteRender


class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music, then notes manages when they should be on-screen.
    """
    BarlineWidth = 0.005
    def __init__(self, graphics:Graphics, note_render: NoteRender, staff: Staff, note_positions: list):
        self.graphics = graphics
        self.note_render = note_render
        self.notes = []
        self.num_barlines = 8
        self.barlines = []
        self.bartimes = []
        self.notes = []
        self.note_positions = note_positions
        self.staff = staff
        self.ref_c4_pos = [Staff.Pos[0], note_positions[60]]
        
        # Create the barlines with 0 being the immovable 0 bar
        staff_width = Staff.StaffSpacing * 4.0
        for i in range(self.num_barlines):
            barline = SpriteShape(self.graphics, [0.1, 0.1, 0.1, 0.75], [0.0, 0.0], [Notes.BarlineWidth, staff_width])
            self.barlines.append(barline)
            self.bartimes.append(i * 32.0)
        
        self.reset()


    def reset(self):
        self.notes = []
        self.rewind()


    def rewind(self):
        """Restore the note pool and barlines to their original state without clearing the music."""
        self.notes_offset = 0
        self.notes_on = {}
        self.note_render.reset()

        for i in range(self.num_barlines):
            self.bartimes[i] = i * 32.0

        self.add_notes_to_render()


    def assign_notes(self, notes: list):
        """Walk in sequence through the notes setting the decoration values for drawing."""
        self.notes = deepcopy(notes)
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

            # Don't add notes that cannot be played
            if note.note not in self.note_positions:
                if GameSettings.DEV_MODE:
                    print(f"Ignoring a note that is out of playable range: {note.note}") 
                self.notes.remove(note)
                num_notes -= 1
                continue
            
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
            def add_all_hats(hats, note_positions):
                # True is stem pointing up
                num_hats = len(hats)
                hat_dir = hats[0].note_drawn < 72 and hats[num_hats -1].note_drawn < 72
                hat_tallest_note = 0 if hat_dir else 999
                straight_hat = True # TODO Handle hats slanting up and down

                # Find the tallest note stem (lowest note)
                hcount = 0
                for h in hats:
                    if hcount < num_hats - 1:
                        if hat_dir:
                            if h.note_drawn > hat_tallest_note:
                                hat_tallest_note = h.note_drawn
                        elif h.note_drawn < hat_tallest_note:
                            hat_tallest_note = h.note_drawn
                    hcount += 1

                if num_hats == 2:
                    hat_note = hats[0]
                    hat_note_next = hats[1]
                    y_diff = note_positions[hat_note_next.note_drawn] - note_positions[hat_note.note_drawn]
                    hat_note.hat = [hat_note.length, y_diff * 0.5]
                    hat_note_next.hat = [0.0, 0.0]
                elif straight_hat:
                    for count in range(num_hats):
                        hat_note = hats[count]
                        hat_note.hat = [hat_note.length, 0.0]
                        if hat_dir:
                            y_diff = note_positions[hat_tallest_note] - note_positions[hat_note.note_drawn]
                        else:
                            y_diff = note_positions[hat_note.note_drawn] - note_positions[hat_tallest_note]
                        hat_note.extra = [0.0, y_diff]
                      
                # Remove the tail from the last note in the chain
                hats[num_hats - 1].hat = [0.0, -1.0]

            if note.length <= 8:
                if hat_num < hat_max:
                    if hat_num <= 1:
                        hats.append(note)
                    else:
                        same_length = hats[hat_num - 1].length == note.length
                        no_rest_between = note.time - hats[hat_num - 1].time == note.length
                        if same_length and no_rest_between and not note.is_rest():
                            hats.append(note)
                        else:
                            add_all_hats(hats, self.note_positions)
                            hats = []
                            hats.append(note)
                
                # 4 notes max in one hat chain
                if len(hats) >= hat_max or note_id == num_notes - 1:
                    add_all_hats(hats, self.note_positions)
                    hats = []
            elif hat_num > 1:
                add_all_hats(hats, self.note_positions)
                hats = []
                            
            note.decorate(get_note_pos(note.time, note.note_drawn), type, decoration, note.hat, note.tie, note.extra)

            bar_time -= note.length
            time += note.length
            note_id += 1
            prev_note = note

        self.add_notes_to_render()
 

    def add_notes_to_render(self, num_notes:int=-1):
        """Add a number of notes to the render queue, -1 meaning add the maximum."""

        notes_len = len(self.notes)
        num_notes = NoteRender.NumNotes // 2 if num_notes < 0 else num_notes
        num_to_add = min(num_notes, notes_len - self.notes_offset)
        for count in range(num_to_add):
            index = self.notes_offset + count
            note = self.notes[index]
            self.note_render.assign(note)
            if GameSettings.DEV_MODE and not note.is_decorated():
                print(f"Error: Undecorated note added to note rendering!")

        self.notes_offset += num_to_add


    def draw(self, dt: float, music_time: float, note_width: float) -> dict:
        """Draw and update the bar lines and all notes on the GPU.
        Return a dictionary keyed on note numbers with value of the end music time note length."""

        # Draw a recycled list of barlines moving from right to left
        for i in range(self.num_barlines):
            bar_start = self.ref_c4_pos[0]
            rel_time = self.bartimes[i] - music_time
            self.barlines[i].pos[0] = bar_start + (rel_time * note_width) - (note_width * 3)
            self.barlines[i].pos[1] = Staff.Pos[1] + Staff.StaffSpacing * 2.0           
            
            if self.barlines[i].pos[0] > bar_start:
                self.barlines[i].draw()

            if self.bartimes[i] < music_time:   
                self.bartimes[i] += self.num_barlines * 32
                          
        # Draw all the notes and return times for the ones that are playing
        self.note_render.draw(dt, music_time, note_width, self.notes_on)

        # Start adding new notes when halfway through the display buffer
        if len(self.notes) > 0 and self.notes_offset < len(self.notes):
            if self.note_render.get_num_free_notes() >= NoteRender.NumNotes // 2 and self.notes[self.notes_offset].time < music_time * 8:
                self.add_notes_to_render()

        return self.notes_on
