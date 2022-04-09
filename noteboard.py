from key_signature import KeySignature
from staff import Staff
from texture import TextureManager
from gui import Gui

class NoteBoard:
    """A class to encapsulate the drawing and calculation of the notes played
       by the player and also by the music notes hitting the playhead.
       """
    BaseAlphaNote = 0.15
    BaseAlphaScore = 0.33

    def __init__(self):
        self.num_notes = 32
        self.origin_note = 48 # C3
        
        # Note box and highlights are the boxes that light up indicating what note should be played
        self.note_box = []
        self.note_highlight = []

        # Score box and highlights are the boxes that light up indicating which notes the player is hitting
        self.score_box = []
        self.score_highlight = []
        
        self.note_positions = []

    def prepare(self, textures: TextureManager, gui: Gui, staff: Staff):
        tone_count = 0
        note_start_x = staff.pos[0] - (staff.width * 0.5) - 0.1
        note_start_y = staff.pos[1] - staff.note_spacing * 3
        score_start_x = note_start_x + 0.071
        for i in range(self.num_notes):
            note_height = staff.note_spacing
            black_key = i in KeySignature.SharpsAndFlats
            if black_key:
                note_height = note_height * 0.5
                
            self.note_highlight.append(NoteBoard.BaseAlphaNote)
            self.score_highlight.append(NoteBoard.BaseAlphaScore)
            note_pos = tone_count * staff.note_spacing
            note_offset = note_start_y + note_pos
            note_size = [staff.note_spacing, note_height]
            score_size = [0.05, staff.note_spacing]

            colour_lookup = i % 12
            if black_key:
                self.note_box.append(gui.add_widget(textures.create_sprite_shape(Staff.NoteColours[colour_lookup], [note_start_x - staff.note_spacing - 0.005, note_offset - staff.note_spacing * 0.5], note_size)))
            else:
                self.note_box.append(gui.add_widget(textures.create_sprite_shape(Staff.NoteColours[colour_lookup], [note_start_x, note_offset], note_size)))
                
            self.score_box.append(gui.add_widget(textures.create_sprite_texture_tinted("score_zone.png", Staff.NoteColours[colour_lookup], [score_start_x, note_offset], score_size)))
            
            self.note_positions.append(note_pos)
            
            if not black_key:
                tone_count += 1

    def get_note_positions(self):
        return self.note_positions

    def set_score(self, note: int):
        score_id = note - self.origin_note
        if score_id >= 0 and score_id < self.num_notes:
            self.score_highlight[score_id] = 1.0

    def set_note(self, note: int):
        highlight_id = note - self.origin_note
        self.note_highlight[highlight_id] = 1.0

    def get_scored_notes(self):
        """Score points for any score box that is highlighted while a note is lit up"""

        scored = False
        scored_notes = zip(self.note_highlight, self.score_highlight)
        for n, s in scored_notes:
            if n >= 1.0 and s >= 1.0:
                self.score = self.score + 10 * self.dt
                scored = True

        return scored, scored_notes
    
    def draw(self, dt: float):
        """Pull the scoring box alpha down to 0"""

        for i in range(self.num_notes):
            self.note_box[i].sprite.set_alpha(self.note_highlight[i])
            self.score_box[i].sprite.set_alpha(self.score_highlight[i])
            self.note_highlight[i] = max(NoteBoard.BaseAlphaNote, self.note_highlight[i] - 0.9 * dt)
            self.score_highlight[i] = max(NoteBoard.BaseAlphaScore, self.score_highlight[i] - 0.8 * dt)
