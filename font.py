from texture import *
from freetype import *
from graphics import *
from OpenGL.GL import *

class Font():
    def __init__(self, filename: str, graphics: Graphics, size: int):
        self.graphics = graphics
        self.face = Face(filename)
        self.face.set_char_size(size)

        # Determine largest glyph size
        width, height, ascender, descender = 0, 0, 0, 0
        for c in range(32,128):
            self.face.load_char( chr(c), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
            bitmap    = self.face.glyph.bitmap
            width     = max( width, bitmap.width )
            ascender  = max( ascender, self.face.glyph.bitmap_top )
            descender = max( descender, bitmap.rows - self.face.glyph.bitmap_top )
        height = ascender+descender
        self.size = [width * 0.1, height * 0.1]

        # Generate texture data
        Z = numpy.zeros((height*6, width*16), dtype=numpy.ubyte)
        for j in range(6):
            for i in range(16):
                self.face.load_char(chr(32+j*16+i), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
                bitmap = self.face.glyph.bitmap
                x = i*width  + self.face.glyph.bitmap_left
                y = j*height + ascender - self.face.glyph.bitmap_top
                Z[y:y+bitmap.rows,x:x+bitmap.width].flat = bitmap.buffer

        # Create OpenGL texture
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, Z.shape[1], Z.shape[0], 0, GL_RGBA, GL_UNSIGNED_BYTE, Z)

        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)
        self.rectangle = numpy.array([-0.5, -0.5, 
                                       0.5, -0.5, 
                                       0.5, 0.5, 
                                      -0.5, 0.5], dtype = numpy.float32)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 32, self.rectangle, GL_STATIC_DRAW) 

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.graphics.indices, GL_STATIC_DRAW)

        self.vertex_pos_id = glGetAttribLocation(graphics.shader_texture, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)
 
        self.tex_coord_id = glGetUniformLocation(graphics.shader_texture, "TexCoord")
        self.colour_id = glGetUniformLocation(graphics.shader_texture, "Colour")
        self.pos_id = glGetUniformLocation(graphics.shader_texture, "Position")
        self.size_id = glGetUniformLocation(graphics.shader_texture, "Size")

        depr = """
        some comment
        dx, dy = width/float(Z.shape[1]), height/float(Z.shape[0])
        base = glGenLists(8*16)
        for i in range(8*16):
            c = chr(i)
            x = i%16
            y = i//16-2
            glNewList(base+i, gl.GL_COMPILE)
            if (c == '\n'):
                glPopMatrix( )
                glTranslatef( 0, -height, 0 )
                glPushMatrix( )
            elif (c == '\t'):
                glTranslatef( 4*width, 0, 0 )
            elif (i >= 32):
                glBegin( gl.GL_QUADS )
                glTexCoord2f( (x  )*dx, (y+1)*dy ), glVertex( 0,     -height )
                glTexCoord2f( (x  )*dx, (y  )*dy ), glVertex( 0,     0 )
                glTexCoord2f( (x+1)*dx, (y  )*dy ), glVertex( width, 0 )
                glTexCoord2f( (x+1)*dx, (y+1)*dy ), glVertex( width, -height )
                glEnd( )
                glTranslatef( width, 0, 0 )
            glEndList( )
        """

    def draw(self, string: str, pos: list, colour: list):
        glUseProgram(self.graphics.shader_font)
        glUniform4f(self.colour_id, colour[0], colour[1], colour[2], colour[3]) 
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.VAO)
        char_pos = pos
        char_size = self.size
        for i in range(len(string)):
            glUniform2f(self.pos_id, char_pos[0], char_pos[1]) 
            glUniform2f(self.size_id, char_size[0], char_size[1]) 
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            char_pos[0] = char_pos[0] + i * 0.05

