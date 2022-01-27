from texture import *
from freetype import *
from graphics import *
from OpenGL.GL import *

class Font():
    def blit(self, dest, src, loc):
        pos = [i if i >= 0 else None for i in loc]
        neg = [-i if i < 0 else None for i in loc]
        target = dest[[slice(i,None) for i in pos]]

        src = src[[slice(i, j) for i,j in zip(neg, target.shape)]]
        target[[slice(None, i) for i in src.shape]] = src
        return dest

    def blit_char(self, dest, glyph, loc, char_index: int):
        bitmap = glyph.bitmap
        width  = bitmap.rows
        height = bitmap.width

        if width <= 0 or height <= 0:
            return loc

        if height > self.largest_glyph_height:
            self.largest_glyph_height = height

        if loc[0] + width >= self.tex_width:
            loc = (0, loc[1] + self.largest_glyph_height)

        if loc[0] > self.tex_width or loc[1] > self.tex_width:
            print(f"Font atlas not large enough for all characters!")
            return loc
            
        src = numpy.reshape(bitmap.buffer, (width, height))
        self.blit(dest, src, loc)

        self.sizes[char_index] = (height / self.tex_width, width / self.tex_height)
        self.positions[char_index] = (loc[1] / self.tex_height, loc[0] / self.tex_width)
        return (loc[0] + width, loc[1])

    def __init__(self, filename: str, graphics: Graphics):
        self.graphics = graphics
        self.face = Face(filename)
        self.face.set_char_size(8000)
        self.sizes = {}
        self.positions = {}
        self.char_start = 32
        self.char_end = 127
        self.num_chars = self.char_end - self.char_start

        # Create one big texture for all the glyphs
        self.tex_width = 2048
        self.tex_height = 2048
        self.image_data = numpy.zeros((self.tex_width, self.tex_height), dtype=numpy.uint8)
        print(f"Building font atlas for {filename} (", end='')

        # Blit font chars into the texture noting the individual char size and tex coords
        atlas_pos = (0, 0)
        self.largest_glyph_height = 0
        for c in range(self.char_start, self.char_end):
            self.face.load_char(chr(c), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT)
            atlas_pos = self.blit_char(self.image_data, self.face.glyph, atlas_pos, c)
            print(chr(c), end='')
        print(")")

        # Generate texture data
        self.image_data_texture = self.image_data.flatten()
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, self.tex_width, self.tex_height, 0, GL_RED, GL_UNSIGNED_BYTE, self.image_data_texture)
        
        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)
        self.rectangle = numpy.array([-0.5, -0.5, 
                                       0.5, -0.5, 
                                       0.5, 0.5, 
                                      -0.5, 0.5, 0.0, 1.0, 1.0, 1.0,1.0, 0.0, 0.0, 0.0], dtype = numpy.float32)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 64, self.rectangle, GL_STATIC_DRAW) 

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.graphics.indices, GL_STATIC_DRAW)

        self.vertex_pos_id = glGetAttribLocation(graphics.shader_font, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)
 
        self.tex_coord_id = glGetAttribLocation(graphics.shader_font, "TexCoord")
        glVertexAttribPointer(self.tex_coord_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(32))
        glEnableVertexAttribArray(self.tex_coord_id)
 
        self.char_coord_id = glGetUniformLocation(graphics.shader_font, "CharCoord")
        self.char_size_id = glGetUniformLocation(graphics.shader_font, "CharSize")
        self.colour_id = glGetUniformLocation(graphics.shader_font, "Colour")
        self.pos_id = glGetUniformLocation(graphics.shader_font, "Position")
        self.size_id = glGetUniformLocation(graphics.shader_font, "Size")

    def draw(self, string: str, font_size: int, pos: list, colour: list):
        glUseProgram(self.graphics.shader_font)
        glUniform4f(self.colour_id, colour[0], colour[1], colour[2], colour[3]) 
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.VAO)
        char_pos = pos
        display_ratio = 0.0025

        for i in range(len(string)):
            c = ord(string[i])

            # Special case for unsupported or space characters
            if c not in self.sizes:
                char_pos = (char_pos[0] + font_size * display_ratio, char_pos[1])
                continue

            tex_coord = self.positions[c]
            tex_size = self.sizes[c]
            char_ratio = tex_size[0] / tex_size[1]

            glUniform4f(self.colour_id, colour[0], colour[1], colour[2], colour[3])
            glUniform2f(self.pos_id, char_pos[0], char_pos[1]) 
            glUniform2f(self.size_id, font_size * display_ratio * char_ratio, font_size * display_ratio) 
            glUniform2f(self.char_coord_id, tex_coord[0], tex_coord[1]) 
            glUniform2f(self.char_size_id, tex_size[0], tex_size[1])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            char_pos = (char_pos[0] + (font_size * display_ratio * tex_size[0] / char_ratio) * 16.0, char_pos[1])

