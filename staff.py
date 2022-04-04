from gui import Gui
from texture import TextureManager

class Staff:
    """Store the data and drawing params of a music graph relationship between pitch and time."""

    NumLines = 4
    DrawColour = [0.075, 0.075, 0.075, 0.8]
    FillColour = [0.78, 0.78, 0.78, 0.75]
    NoteColours = [[0.98, 0.25, 0.22, 1.0], [1.0, 0.33, 0.30, 1.0], [0.78, 0.55, 0.99, 1.0], [0.89, 173, 255, 1.0], [1.0, 0.89, 63, 1.0], [0.39, 0.39, 0.55, 1.0], [0.47, 0.47, 0.67, 1.0],  # C4, Db4, D4, Eb4, E4, F4, Gb4
                   [0.89, 0.97, 1.0, 1.0], [0.95, 1.0, 1.0, 1.0], [0.67, 0.1, 0.01, 1.0], [0.78, 0.18, 0.09, 1.0], [0, 0.78, 1.0, 1.0], [1.0, 0.39, 1, 1.0], [1.0, 0.47, 0.1, 1.0],       # G4, Ab4, A4, Bb4, B4, C5, Db5
                   [1.0, 0.375, 0.89, 1.0], [1.0, 0.48, 1.0, 1.0], [0.19, 0.78, 0.19, 1.0], [0.54, 0.53, 0.55, 1.0], [0.54, 0.53, 0.55, 1.0], [0.29, 0.29, 0.98, 1.0]]                   # D5, Eb5, E5, F5, Gb5, G5

    def __init__(self):
        self.pos = [0.15, 0.0]
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