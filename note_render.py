from pathlib import Path
from OpenGL.GL import (
    glGetUniformLocation,
    glUniform1iv,
    glUniform1f, 
    glUniform1fv, glUniform2fv, glUniform4fv,
)

from gamejam.settings import GameSettings
from gamejam.graphics import Graphics, Shader, ShaderType
from gamejam.texture import SpriteTexture, Texture

from staff import Staff
from note import Note
from key_signature import KeySignature
from staff import Staff


class NoteRender:
    """Draw 32 notes at a time for the entire game on the GPU."""
    NumNotes = 32
    BaseColour = 0.11
    HitColour = [BaseColour, 0.78, BaseColour, 1.0]
    MissColour = [0.78, BaseColour, BaseColour, 1.0]

    def __init__(self, graphics: Graphics, staff: Staff):
        self.staff = staff
        self.calibration = False
        self.display_ratio = graphics.display_ratio
        self.ref_c4_pos = [Staff.Pos[0], staff.note_positions[60]]
        self.note_width = Staff.NoteWidth32nd
        self.reset()

        # Notation shader draws from 0->1 on XY, left->right, down->up
        shader_substitutes = {
            "NUM_NOTES": NoteRender.NumNotes,
            "NUM_KEY_SIG": KeySignature.NumAccidentals,
            "#define staff_pos_x 0.0": f"#define staff_pos_x {0.5 + Staff.Pos[0] * 0.5}",
            "#define staff_pos_y 0.5": f"#define staff_pos_y {0.5 + Staff.Pos[1] * 0.5}",
            "#define staff_width 1.0": f"#define staff_width {Staff.Width * 0.5}",
            "#define staff_note_spacing 0.03": f"#define staff_note_spacing {Staff.NoteSpacing * 0.5}"
        }
        note_shader_path = Path(__file__).parent / "ext" / "shaders" / "notes.frag"
        note_shader = Graphics.process_shader_source(Graphics.load_shader(note_shader_path), shader_substitutes)
        self.shader = Graphics.create_program(graphics.builtin_shader(Shader.TEXTURE, ShaderType.VERTEX), note_shader)
        
        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.music_time_id = glGetUniformLocation(self.shader, "MusicTime")
        self.key_positions_id = glGetUniformLocation(self.shader, "KeyPositions")
        self.note_positions_id = glGetUniformLocation(self.shader, "NotePositions")
        self.note_colours_id = glGetUniformLocation(self.shader, "NoteColours")
        self.note_types_id = glGetUniformLocation(self.shader, "NoteTypes")
        self.note_decoration_id = glGetUniformLocation(self.shader, "NoteDecoration")
        self.note_hats_id = glGetUniformLocation(self.shader, "NoteHats")
        self.note_ties_id = glGetUniformLocation(self.shader, "NoteTies")
        self.note_extra_id = glGetUniformLocation(self.shader, "NoteExtra")


    def reset(self):
        self.note = -1
        self.notes_assigned = 0
        self.notes = [None] * NoteRender.NumNotes
        self.note_positions = [0.0] * NoteRender.NumNotes * 2
        self.note_colours = [0.0] * NoteRender.NumNotes * 4
        self.note_types = [0] * NoteRender.NumNotes
        self.note_decoration = [0] * NoteRender.NumNotes
        self.note_hats = [0.0] * NoteRender.NumNotes * 2
        self.note_ties = [0.0] * NoteRender.NumNotes
        self.note_extra = [0.0] * NoteRender.NumNotes * 2
        

    def _assign_calibration_notes(self):
        """Add five notes with separate colours to each extent of the screen."""

        self.calibration = True
        npos = 0
        cpos = 0

        def add_calibration_note(npos, cpos, pos: list, col: list):
            self.note +=1
            self.notes_assigned += 1
            self.notes[self.note] = Note(60, 0, 32)
            self.note_positions[npos] = pos[0]
            self.note_positions[npos + 1] = pos[1]
            self.note_colours[cpos] = col[0]
            self.note_colours[cpos+1] = col[1]
            self.note_colours[cpos+2] = col[2]
            self.note_colours[cpos+3] = col[3]
            self.note_types[self.note] = 1
            return npos + 2, cpos + 4

        npos, cpos = add_calibration_note(npos, cpos, [-1.0, -1.0], [1.0, 0.0, 0.0, 1.0])
        npos, cpos = add_calibration_note(npos, cpos, [1.0, -1.0], [0.0, 1.0, 0.0, 1.0])
        npos, cpos = add_calibration_note(npos, cpos, [1.0, 1.0], [0.0, 0.0, 1.0, 1.0])
        npos, cpos = add_calibration_note(npos, cpos, [-1.0, 1.0], [1.0, 1.0, 0.0, 1.0])
        npos, cpos = add_calibration_note(npos, cpos, [0.0, 0.0], [1.0, 0.0, 1.0, 1.0])


    def get_num_free_notes(self):
        return NoteRender.NumNotes - self.notes_assigned
        

    def assign(self, note: Note):
        """Add a new note to an empty note slot."""

        search = 0
        new_note = (self.note + 1) % NoteRender.NumNotes
        while self.notes[new_note] is not None:
            search += 1
            new_note = (self.note + search) % NoteRender.NumNotes
            if search >= NoteRender.NumNotes // 2:
                if GameSettings.DEV_MODE:
                    print(f"Note render has run out of active notes!")
                break
        
        self.note = new_note
        self.notes_assigned += 1
        self.notes[self.note] = note

        col = [NoteRender.BaseColour, NoteRender.BaseColour, NoteRender.BaseColour, 1.0]

        npos = self.note * 2
        cpos = self.note * 4
        self.note_positions[npos] = note.pos[0]
        self.note_positions[npos + 1] = note.pos[1]
        self.note_colours[cpos] = col[0]
        self.note_colours[cpos+1] = col[1]
        self.note_colours[cpos+2] = col[2]
        self.note_colours[cpos+3] = col[3]
        self.note_types[self.note] = int(note.type.value)
        self.note_decoration[self.note] = int(note.decoration.value)
        self.note_hats[npos] = note.hat[0] * self.note_width * 0.5 # TODO Move note_width into a uniform so hats join up when zooming
        self.note_hats[npos + 1] = note.hat[1]
        self.note_ties[self.note] = note.tie
        self.note_extra[npos] = note.extra[0]
        self.note_extra[npos + 1] = note.extra[1]


    def draw(self, dt: float, music_time: float, note_width: float, notes_on: dict) -> dict:
        """Process note timing then upload the note data state to the shader every frame."""
        
        self.note_width = note_width

        if not self.calibration:
            for i in range(NoteRender.NumNotes):
                note = self.notes[i]
                npos = i * 2
                cpos = i * 4
                should_be_displayed = note is not None and note.time - music_time < 32 * 8
                if should_be_displayed:
                    self.note_colours[cpos + 3] = 1.0
                    self.note_positions[npos] = self.ref_c4_pos[0] + ((note.time - music_time) * note_width)

                    # Hold the visuals a 32nd note longer so the player can see which note to play
                    should_be_played = note.time <= music_time and not note.is_rest()
                    should_be_recycled = note.time + 1 < music_time
                    if should_be_played:
                        self.note_colours[cpos + 1] = NoteRender.HitColour[1]
                    else:
                        self.note_colours[cpos + 1] = NoteRender.BaseColour

                    # Note is on as soon as it hits the playhead 
                    if should_be_played:
                        note_off_time = music_time + note.length
                        if note.note in notes_on:
                            # Dictionary entry will be a list if there are repeated notes
                            if isinstance(notes_on[note.note], list):
                                notes_on[note.note].append(note_off_time)
                            else:
                                notes_on[note.note] = [notes_on[note.note], note_off_time]
                        else:
                            notes_on[note.note] = note_off_time

                    if should_be_recycled:
                        self.note_positions[npos] = -99.0
                        self.note_colours[cpos + 3] = 0.0
                        self.notes[i] = None
                        self.notes_assigned -= 1
                else:
                    self.note_colours[cpos + 3] = 0.0

        def note_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform1f(self.music_time_id, music_time)
            glUniform2fv(self.key_positions_id, KeySignature.NumAccidentals, self.staff.key_signature.positions)
            glUniform2fv(self.note_positions_id, NoteRender.NumNotes, self.note_positions)
            glUniform4fv(self.note_colours_id, NoteRender.NumNotes, self.note_colours)
            glUniform1iv(self.note_types_id, NoteRender.NumNotes, self.note_types)
            glUniform1iv(self.note_decoration_id, NoteRender.NumNotes, self.note_decoration)
            glUniform2fv(self.note_hats_id, NoteRender.NumNotes, self.note_hats)
            glUniform1fv(self.note_ties_id, NoteRender.NumNotes, self.note_ties)
            glUniform2fv(self.note_extra_id, NoteRender.NumNotes, self.note_extra)
        
        self.sprite.draw(note_uniforms)

        return notes_on

    def end(self):
        pass
