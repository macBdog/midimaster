from gui import Gui
from texture import TextureManager

class Staff:
    """Data and drawing params for a music graph relationship between pitch and time."""

    NumLines = 4
    DrawColour = [0.075, 0.075, 0.075, 0.8]
    FillColour = [0.78, 0.78, 0.78, 0.75]
    NoteSpacing = 0.085
    StaffSpacing = NoteSpacing * 2
    OctaveSpacing = NoteSpacing * 7

    def __init__(self):
        self.pos = [0.15, 0.1]
        self.width = 1.85
        self.barline_height = 0.02
        
    def prepare(self, gui:Gui, textures:TextureManager):
        """Add the 12 note lines with the staff lines of the treble clef highlighted to a gui."""
        
        self.lines = []
        self.lines.append(gui.add_widget(textures.create_sprite_shape(Staff.DrawColour, [self.pos[0], self.pos[1] - Staff.NoteSpacing + 4 * Staff.StaffSpacing], [self.width, self.barline_height])))
        for i in range(Staff.NumLines):
            staff_body_white = textures.create_sprite_shape(Staff.FillColour, [self.pos[0], self.pos[1] + i * Staff.StaffSpacing], [self.width, Staff.StaffSpacing - self.barline_height])
            staff_body_black = textures.create_sprite_shape(Staff.DrawColour, [self.pos[0], self.pos[1] - Staff.NoteSpacing + i * Staff.StaffSpacing], [self.width, self.barline_height])
            self.lines.append(gui.add_widget(staff_body_white))
            self.lines.append(gui.add_widget(staff_body_black))