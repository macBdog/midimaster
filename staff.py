from gui import Gui
from texture import TextureManager

class Staff:
    """Store the data and drawing params of a music graph relationship between pitch and time."""

    NumLines = 4
    DrawColour = [0.075, 0.075, 0.075, 0.8]
    FillColour = [0.78, 0.78, 0.78, 0.75]

    def __init__(self):
        self.pos = [0.15, 0.1]
        self.ref_note = 60                            # Using C4 as reference note
        self.ref_note_pos = [0.0, self.pos[1] - 0.33] # Draw position of reference note
        self.width = 1.85
        self.note_spacing = 0.085
        self.staff_spacing = self.note_spacing * 2
        self.barline_height = 0.02
        
    def prepare(self, gui:Gui, textures:TextureManager):
        """Add the 12 note lines with the staff lines of the treble clef highlighted to a gui."""
        
        self.lines = []
        self.lines.append(gui.add_widget(textures.create_sprite_shape(Staff.DrawColour, [self.pos[0], self.pos[1] - self.note_spacing + 4 * self.staff_spacing], [self.width, self.barline_height])))
        for i in range(Staff.NumLines):
            staff_body_white = textures.create_sprite_shape(Staff.FillColour, [self.pos[0], self.pos[1] + i * self.staff_spacing], [self.width, self.staff_spacing - self.barline_height])
            staff_body_black = textures.create_sprite_shape(Staff.DrawColour, [self.pos[0], self.pos[1] - self.note_spacing + i * self.staff_spacing], [self.width, self.barline_height])
            self.lines.append(gui.add_widget(staff_body_white))
            self.lines.append(gui.add_widget(staff_body_black))