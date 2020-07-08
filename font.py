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

        # Generate texture data
        Z = numpy.zeros((height*6, width*16), dtype=numpy.ubyte)
        for j in range(6):
            for i in range(16):
                self.face.load_char(chr(32+j*16+i), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
                bitmap = self.face.glyph.bitmap
                x = i*width  + self.face.glyph.bitmap_left
                y = j*height + ascender - self.face.glyph.bitmap_top
                Z[y:y+bitmap.rows,x:x+bitmap.width].flat = bitmap.buffer

        # Bound texture
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR )
        # glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, Z.shape[1], Z.shape[0], 0, GL_RGBA, GL_UNSIGNED_BYTE, Z )

        # Generate display lists
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

    def draw(self, pos: tuple, colour: tuple, string: str):
        glUseProgram(self.graphics.shader_texture)
        glActiveTexture(GL_TEXTURE0)
