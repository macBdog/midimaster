from gui import Gui
from texture import TextureManager
from key_signature import KeySignature

class Staff:
    """A class to encapsulate:
        A music graph relationship between pitch and time. 
        Notes activated by the player at any time.
        Notes by the score notes hitting the playhead.
       """
    ScoreBoxTexture = "score_zone.png"
    OriginNote = 48 # C3
    NumNotes = 36
    BaseAlphaNote = 0.35
    BaseAlphaScore = 0.33
    NoteColours = [[31, 130, 180, 1.0],    [166, 206, 227, 1.0],    [51, 166, 44, 1.0],  [178, 223, 138, 1.0], # C, Db, D, Eb 
                    [227, 26, 28, 1.0],     [255, 127, 0.0, 1.0],    [253, 191, 111, 1.0], [106, 61, 154, 1.0], # E, F Gb, G
                    [255, 107, 225, 1.0],   [255, 0, 229, 1.0],      [255, 255, 153, 1.0], [177, 89, 40, 1.0]]# Ab, A, Bb, B 
    Width = 1.85
    Pos = [-1.0 + (2.0 - Width), 0.0]    
    DrawColour = [0.075, 0.075, 0.075, 0.8]
    FillColour = [0.78, 0.78, 0.78, 0.75]
    NoteWidth32nd = 0.02
    NoteSpacing = 0.055
    StaffSpacing = NoteSpacing * 2
    OctaveSpacing = NoteSpacing * 7

    def __init__(self):
        self.key_signature = KeySignature()
        Staff.NoteColours = [[i / 255 for i in j] for j in Staff.NoteColours]

        # Note box and highlights are the boxes that light up indicating what note should be played when a note hits it
        self.note_box = []
        self.note_highlight = []

        # Score box and highlights are the boxes that light up indicating which notes the player is inputting
        self.score_box = []
        self.score_highlight = []
        
        self.note_positions = {}
        self.playing_notes = {}
        
    def prepare(self, gui:Gui, textures:TextureManager):
        """Calculate and add two rows of virtual keys aligned with the staff drawn separately.
        [black_keys]            [score box]
                    [white_keys][score box]
        [black_keys]            [score box]
                    [white_keys][score box]
        """
        
        tone_count = 0
        total_width = 2.0 - Staff.Width
        box_width = total_width / 3.0
        note_black_key_start_x = -1.0 + (box_width * 0.5)
        note_start_x = -1.0 + (box_width * 1.5)
        score_start_x = -1.0 + (box_width * 2.5)
        note_start_y = Staff.Pos[1] - Staff.NoteSpacing * (12 - 3)
        for i in range(Staff.NumNotes):
            note_height = Staff.NoteSpacing
            score_height = Staff.NoteSpacing
            note = Staff.OriginNote + i
            note_lookup = note % 12
            black_key = note_lookup in KeySignature.SharpsAndFlats
            black_key_height = note_height * 0.5 
            black_key_next = note_lookup + 1 in KeySignature.SharpsAndFlats
            black_key_prev = note_lookup - 1 in KeySignature.SharpsAndFlats

            self.note_highlight.append(Staff.BaseAlphaNote)
            self.score_highlight.append(Staff.BaseAlphaScore)
            note_pos = note_start_y + (tone_count * Staff.NoteSpacing)
            score_pos = note_pos

            # Determine the heights and Y positions of the note and score elements
            if black_key:
                note_height = black_key_height
                score_height = black_key_height
            else:
                if black_key_next and black_key_prev:
                    score_height -= black_key_height
                elif black_key_next and not black_key_prev:
                    score_height -= black_key_height * 0.5
                    score_pos -= black_key_height * 0.25
                elif black_key_prev and not black_key_next:
                    score_height -= black_key_height * 0.5
                    score_pos += black_key_height * 0.25

            note_size = [box_width, note_height]
            score_size = [box_width, score_height]

            if black_key:
                self.note_box.append(gui.add_widget(textures.create_sprite_shape(Staff.NoteColours[note_lookup], [note_black_key_start_x, note_pos - Staff.NoteSpacing * 0.5], note_size)))
                self.score_box.append(gui.add_widget(textures.create_sprite_texture_tinted(Staff.ScoreBoxTexture, Staff.NoteColours[note_lookup], [score_start_x, score_pos - Staff.NoteSpacing * 0.5], score_size)))
            else:
                self.note_box.append(gui.add_widget(textures.create_sprite_shape(Staff.NoteColours[note_lookup], [note_start_x, note_pos], note_size)))
                self.score_box.append(gui.add_widget(textures.create_sprite_texture_tinted(Staff.ScoreBoxTexture, Staff.NoteColours[note_lookup], [score_start_x, score_pos], score_size)))
            
            self.note_positions[note] = note_pos
            
            if not black_key:
                tone_count += 1

    def get_note_positions(self):
        """:return: A dictionary of absolute note Y positions keyed by MIDI note id centered in the staff"""
        return self.note_positions

    def set_score(self, note: int):
        score_id = note - Staff.OriginNote
        if score_id >= 0 and score_id < Staff.NumNotes:
            self.score_highlight[score_id] = 1.0

    def note_on(self, note: int):
        self.playing_notes[note] = True
        highlight_id = note - Staff.OriginNote
        self.note_highlight[highlight_id] = 1.0
    
    def note_off(self, note: int):
        del self.playing_notes[note]

    def get_playing_notes(self):
        return self.playing_notes

    def is_scoring(self):
        """Are there notes playing in the music and the input at the same time.
        :return: bool True if matching staff and scoreboard id of simultaneously held notes."""

        for _, (n, s) in enumerate(zip(self.note_highlight, self.score_highlight)):
            if n >= 1.0 and s >= 1.0:
                return True

        return False
    
    def draw(self, dt: float):
        """Pull the playing note and scoring box alpha down to 0"""

        for i in range(Staff.NumNotes):
            self.note_box[i].sprite.set_alpha(self.note_highlight[i])
            self.score_box[i].sprite.set_alpha(self.score_highlight[i])
            self.note_highlight[i] = max(Staff.BaseAlphaNote, self.note_highlight[i] - 0.8 * dt)
            self.score_highlight[i] = max(Staff.BaseAlphaScore, self.score_highlight[i] - 0.7 * dt)

