from key_signature import KeySignature
from staff import Staff
from texture import TextureManager
from gui import Gui

class NoteBoard:
    """A class to encapsulate the drawing and calculation of the notes played
       by the player and also by the music notes hitting the playhead.
       """
    ScoreBoxTexture = "score_zone.png"
    BaseAlphaNote = 0.35
    BaseAlphaScore = 0.33
    NoteColours = [[31, 130, 180, 1.0],    [166, 206, 227, 1.0],    [51, 166, 44, 1.0],  [178, 223, 138, 1.0], # C, Db, D, Eb 
                    [227, 26, 28, 1.0],     [255, 127, 0.0, 1.0],    [253, 191, 111, 1.0], [106, 61, 154, 1.0], # E, F Gb, G
                    [255, 107, 225, 1.0],   [255, 0, 229, 1.0],      [255, 255, 153, 1.0], [177, 89, 40, 1.0]]# Ab, A, Bb, B 

    def __init__(self):
        NoteBoard.NoteColours = [[i / 255 for i in j] for j in NoteBoard.NoteColours]
        self.num_notes = 36
        self.origin_note = 48 # C3
        
        # Note box and highlights are the boxes that light up indicating what note should be played when a note hits it
        self.note_box = []
        self.note_highlight = []

        # Score box and highlights are the boxes that light up indicating which notes the player is inputting
        self.score_box = []
        self.score_highlight = []
        
        self.note_positions = []

    def prepare(self, textures: TextureManager, gui: Gui, staff: Staff):
        tone_count = 0
        note_start_x = staff.pos[0] - (staff.width * 0.5) - 0.1
        note_start_y = staff.pos[1] - staff.note_spacing * (12 - 2)
        score_start_x = note_start_x + 0.071
        for i in range(self.num_notes):
            note_height = staff.note_spacing
            score_height = staff.note_spacing
            note_lookup = i % 12
            black_key = note_lookup in KeySignature.SharpsAndFlats
            black_key_height = note_height * 0.5 
            black_key_next = note_lookup + 1 in KeySignature.SharpsAndFlats
            black_key_prev = note_lookup - 1 in KeySignature.SharpsAndFlats

            self.note_highlight.append(NoteBoard.BaseAlphaNote)
            self.score_highlight.append(NoteBoard.BaseAlphaScore)
            note_pos = tone_count * staff.note_spacing
            note_offset = note_start_y + note_pos
            score_offset = note_offset

            # Determine the heights and Y positions of the note and score elements
            if black_key:
                note_height = black_key_height
                score_height = black_key_height
            else:
                if black_key_next and black_key_prev:
                    score_height -= black_key_height * 0.5
                elif black_key_next and not black_key_prev:
                    score_height -= black_key_height * 0.25
                    score_offset -= black_key_height * 0.25
                elif black_key_prev and not black_key_next:
                    score_height -= black_key_height * 0.25
                    score_offset += black_key_height * 0.25

            note_size = [staff.note_spacing, note_height]
            score_size = [0.05, score_height]

            if black_key:
                self.note_box.append(gui.add_widget(textures.create_sprite_shape(NoteBoard.NoteColours[note_lookup], [note_start_x - staff.note_spacing - 0.005, note_offset - staff.note_spacing * 0.5], note_size)))
                self.score_box.append(gui.add_widget(textures.create_sprite_texture_tinted(NoteBoard.ScoreBoxTexture, NoteBoard.NoteColours[note_lookup], [score_start_x, score_offset - staff.note_spacing * 0.5], score_size)))
            else:
                self.note_box.append(gui.add_widget(textures.create_sprite_shape(NoteBoard.NoteColours[note_lookup], [note_start_x, note_offset], note_size)))
                self.score_box.append(gui.add_widget(textures.create_sprite_texture_tinted(NoteBoard.ScoreBoxTexture, NoteBoard.NoteColours[note_lookup], [score_start_x, score_offset], score_size)))
            
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
                scored = True

        return scored, scored_notes
    
    def draw(self, dt: float):
        """Pull the scoring box alpha down to 0"""

        for i in range(self.num_notes):
            self.note_box[i].sprite.set_alpha(self.note_highlight[i])
            self.score_box[i].sprite.set_alpha(self.score_highlight[i])
            self.note_highlight[i] = max(NoteBoard.BaseAlphaNote, self.note_highlight[i] - 0.9 * dt)
            self.score_highlight[i] = max(NoteBoard.BaseAlphaScore, self.score_highlight[i] - 0.8 * dt)