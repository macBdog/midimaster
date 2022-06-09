from settings import GameSettings
from graphics import Graphics
from OpenGL.GL import *

from texture import SpriteTexture, Texture
from note import Note
from staff import Staff

class NoteRender:
    """Draw 32 notes at a time for the entire game on the GPU."""
    NumNotes = 32

    PIXEL_SHADER_NOTES = """
    #version 430

    in vec2 OutTexCoord;
    out vec4 outColour;

    uniform sampler2D SamplerTex;
    uniform vec4 Colour;
    uniform float DisplayRatio;

    uniform vec2 NotePositions[NUM_NOTES];
    uniform vec4 NoteColours[NUM_NOTES];
    uniform int NoteTypes[NUM_NOTES];
    uniform int NoteDecoration[NUM_NOTES];
    uniform vec2 NoteTails[NUM_NOTES];
    uniform float NoteTies[NUM_NOTES];

    #define antialias 0.08
    #define note_size 0.1
    #define note_slant vec2(0.33,0.93496)
    #define note_slant_alt vec2(0.73, 0.73)
    #define note_spacing_32nd 0.015

    #define note_type_whole 1
    #define note_type_half 2
    #define note_type_quarter 3
    #define note_type_eighth 4
    #define note_type_sixteenth 4

    #define dec_dotted 1
    #define dec_accent 2
    #define dec_natural 3
    #define dec_sharp 4
    #define dec_flat 5

    float drawCircle(in vec2 uv, vec2 center, float radius)
    {
        vec2 d1 = uv - center;
        vec2 d2 = d1;
        return smoothstep(radius, radius - (antialias * 0.02), dot(d1, d2) * 100.0);
    }

    float drawEllipse(in vec2 uv, in vec2 pos, vec2 dim) 
    {
        vec2 d = (uv - pos);
        d.x /= dot(vec2(dim.x, 0.0), vec2(dim.x, 0.0));
        d.y /= dot(vec2(0.0, dim.y), vec2(0.0, dim.y));

        if (abs( d.x ) <= 1.0 && abs( d.y ) < 1.0 ) 
        {
            if (dot(d, d) < 1.0) return 1.0;
        }
        0.0;
    }

    float drawRotatedEllipse(vec2 uv, vec2 pos, float size, bool altRot)
    {
        float dim = 70.0;
        pos *= vec2(dim, dim);
        vec2 diff = note_slant * size;
        if (altRot)
        {
            diff = note_slant_alt * size;
        }
        vec2 l = pos - diff;
        vec2 r = pos + diff;
        
        vec2 coord = uv * vec2(dim,  dim);

        return smoothstep(0.0, antialias, distance(l, r) + 1.0 - (distance(coord, l) + distance(coord, r)));
    }

    float drawRect(in vec2 uv, in vec2 center, in vec2 wh)
    {
        vec2 disRec = abs(uv - center) - wh * 0.5;
        float dis = max(disRec.x, disRec.y);
        return clamp(float(dis < 0.0), 0.0, 1.0);
    }

    float distanceToSegment( vec2 a, vec2 b, vec2 p )
    {
    vec2 pa = p - a, ba = b - a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    return length( pa - ba*h );
    }

    float drawLineRounded(in vec2 uv, in vec2 start, in vec2 end, in float width)
    {
        return mix(0.0, 1.0, 1.0-smoothstep(width-antialias*0.02,width, distanceToSegment(start, end, uv)));
    }

    float drawLineSquare(in vec2 uv, in vec2 start, in vec2 end, in float width)
    {
        float col = 0.0;
        vec2 clip_box = vec2(0.015, width * 4.0);
        float line = mix(0.0, 1.0, 1.0-smoothstep(width-antialias*0.01,width, distanceToSegment(start, end, uv)));
        float leftBox = drawRect(uv, start + vec2(clip_box.x * -0.5, 0.0), clip_box);
        float rightBox = drawRect(uv, end + vec2(clip_box.x * 0.5, 0.0), clip_box);
        col = line - leftBox - rightBox;
        return clamp(col, 0.0, 1.0);
    }

    float drawTie(in vec2 uv, in vec2 start, in vec2 end)
    {
        float col = 0.0;
        vec2 dir = (end - start);
        float elen = length(dir);
        vec2 mid = start + (dir * 0.5) + vec2(-0.004, clamp(elen - 0.2, 0.0, 0.1) - 0.035);
        vec2 dim_lo = vec2(elen * 1.45, elen * 0.99);
        vec2 dim_hi = vec2(dim_lo.x * 1.15, dim_lo.y * 1.15);
        vec2 offset_inner = vec2(0.0, elen * 0.11);
        col += drawEllipse(uv, mid, dim_lo) - drawEllipse(uv, mid + offset_inner, dim_hi);
        return clamp(col, 0.0, 1.0);
    }

    float drawNote(in vec2 uv, in vec2 p, in int note_type, in int dec, in vec2 tail_size, in float tie_32s) 
    {
        vec2 stalk_size = vec2(0.0025, 0.2);
        float blob_size = 1.6;
        float blob = drawRotatedEllipse(uv, p, blob_size, false);
        float decoration = 0.0;
        if (dec == 1)
        {
            decoration += drawEllipse(uv, p + vec2(0.04, 0.0), vec2(0.07, 0.1));
        }
        
        float tie = 0.0;
        if (tie_32s > 0.0)
        {
            tie = drawTie(uv, p, p + vec2(note_spacing_32nd * tie_32s, 0.0));
        }
        
        if (note_type <= note_type_half)
        {
            blob -= drawRotatedEllipse(uv, p, blob_size * 0.5, true);
        }
        
        if (note_type == note_type_whole)
        {
            return clamp(blob + tie + decoration, 0.0, 1.0);
        }
        
        float stalk_width = note_size * 0.184;
        vec2 stalk_pos = vec2(stalk_width, stalk_size.y * 0.5);
        float stalk = drawRect(uv, p + stalk_pos, stalk_size);
        
        if (note_type <= note_type_quarter)
        {
            return clamp(blob + tie + stalk + decoration, 0.0, 1.0);
        }
        
        float tail_width = 0.012;
        vec2 tail_start = p + stalk_pos + vec2(stalk_width * -0.05, (stalk_size.y * 0.51) - tail_width);
        vec2 tail_end = tail_start + tail_size + vec2(0.002, 0.0);
        float tail = drawLineSquare(uv, tail_start, tail_end, tail_width);
        
        return clamp(blob + tie + stalk + tail + decoration, 0.0, 1.0);   
    }

    vec4 drawNotes(in vec2 uv)
    {
        vec4 all_notes = vec4(0.0);
        for (int i = 0; i < NUM_NOTES; ++i)
        {
            vec2 note_pos = (NotePositions[i] + 1.0) * 0.5;
            float note = drawNote(uv, note_pos, NoteTypes[i], NoteDecoration[i], NoteTails[i], NoteTies[i]);
            float alpha = NoteColours[i].a;
            all_notes += vec4(note * NoteColours[i].xyz, note.r * alpha);
        }
        return all_notes;
    }

    void main()
    {
        vec2 uv = OutTexCoord;
        uv.y = 1.0 - uv.y;

        outColour = vec4(drawNotes(uv));
    }
    """.replace("NUM_NOTES", str(NumNotes))

    def __init__(self, graphics: Graphics, display_ratio: float, ref_c4_pos: list):
        self.calibration = False
        self.display_ratio = 1.0 / display_ratio
        self.ref_c4_pos = ref_c4_pos
        self.note = -1
        self.notes = [None] * NoteRender.NumNotes
        self.note_positions = [0.0] * NoteRender.NumNotes * 2
        self.note_colours = [0.0] * NoteRender.NumNotes * 4
        self.note_types = [0] * NoteRender.NumNotes
        self.note_decoration = [0] * NoteRender.NumNotes
        self.note_tails = [0.0] * NoteRender.NumNotes * 2
        self.note_ties = [0.0] * NoteRender.NumNotes

        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_TEXTURE, GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(NoteRender.PIXEL_SHADER_NOTES, GL_FRAGMENT_SHADER)
        )

        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.music_time_id = glGetUniformLocation(self.shader, "MusicTime")
        self.note_positions_id = glGetUniformLocation(self.shader, "NotePositions")
        self.note_colours_id = glGetUniformLocation(self.shader, "NoteColours")
        self.note_types_id = glGetUniformLocation(self.shader, "NoteTypes")
        self.note_decoration_id = glGetUniformLocation(self.shader, "NoteDecoration")
        self.note_tails_id = glGetUniformLocation(self.shader, "NoteTails")
        self.note_ties_id = glGetUniformLocation(self.shader, "NoteTies")

    def _assign_calibration_notes(self):
        """Add five notes with separate colours to each extent of the screen."""

        self.calibration = True
        npos = 0
        cpos = 0

        def add_calibration_note(npos, cpos, pos: list, col: list):
            self.note +=1
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

    def assign(self, note: Note, pos: list, type: int, decoration: int, tail: list, tie: float):
        """Add a new note to an empty note slot."""

        search = 0
        new_note = (self.note + 1) % NoteRender.NumNotes
        while self.notes[new_note] is not None:
            search += 1
            new_note = (self.note + search) % NoteRender.NumNotes
            if search >= NoteRender.NumNotes:
                if GameSettings.DEV_MODE:
                    print(f"Note render has run out of active notes!")
                break
        
        self.note = new_note
        self.notes[self.note] = note

        col = [0.1, 0.1, 0.1, 1.0]

        npos = self.note * 2
        cpos = self.note * 4
        self.note_positions[npos] = pos[0]
        self.note_positions[npos + 1] = pos[1]
        self.note_colours[cpos] = col[0]
        self.note_colours[cpos+1] = col[1]
        self.note_colours[cpos+2] = col[2]
        self.note_colours[cpos+3] = col[3]
        self.note_types[self.note] = type
        self.note_decoration[self.note] = decoration
        self.note_tails[npos] = tail[0]
        self.note_tails[npos + 1] = tail[1]
        self.note_ties[self.note] = tie

    def draw(self, dt: float, music_time: float, note_width: float, notes_on: dict) -> dict:
        """Process note timing then upload the note data state to the shader every frame."""
        
        for i in range(NoteRender.NumNotes):
            note = self.notes[i]
            should_be_displayed = note is not None and note.time - music_time < 32 * 4
            if should_be_displayed and not self.calibration:
                npos = i * 2
                cpos = i * 4
                self.note_positions
                self.note_positions[npos] = self.ref_c4_pos[0] + ((note.time - music_time) * note_width)

                # Hold the visuals a 32note longer so the player can see which note to play
                should_be_played = note.time <= music_time
                should_be_recycled = note.time + 1 < music_time
                if should_be_played:
                    self.note_colours[cpos + 1] = 0.78
                else:
                    self.note_colours[cpos + 1] = 0.1

                note_lookup = note.note % 12
                num_under = Note.NoteLineLookupUnder[note_lookup]
                num_over = Note.NoteLineLookupOver[note_lookup]
                line_y_offset = 0.025 if num_under <= 1 or note_lookup < 60 else 0.012
                line_x_offset = -0.019
                for j in range(num_under):
                    pass
                    #self.font.draw('_', 82, [note_pos[0] + line_x_offset, self.ref_c4_pos[1] + line_y_offset - (i * Staff.NoteSpacing * 2)], note_col)

                for j in range(num_over):
                    pass
                    #self.font.draw('_', 82, [note_pos[0] + line_x_offset, self.ref_c4_pos[1] + line_y_offset + (Staff.NoteSpacing * 12) - (i * Staff.NoteSpacing * 2)], note_col)
                    
                # Note is on as soon as it hits the playhead
                if should_be_played:
                    notes_on[self.note] = music_time + note.length

                if should_be_recycled:
                    self.notes[i] = None

        def note_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform1f(self.music_time_id, music_time)
            glUniform2fv(self.note_positions_id, NoteRender.NumNotes, self.note_positions)
            glUniform4fv(self.note_colours_id, NoteRender.NumNotes, self.note_colours)
            glUniform1iv(self.note_types_id, NoteRender.NumNotes, self.note_types)
            glUniform1iv(self.note_decoration_id, NoteRender.NumNotes, self.note_decoration)
            glUniform2fv(self.note_tails_id, NoteRender.NumNotes, self.note_tails)
            glUniform1fv(self.note_ties_id, NoteRender.NumNotes, self.note_ties)
        
        self.sprite.draw(note_uniforms)

    def end(self):
        pass
