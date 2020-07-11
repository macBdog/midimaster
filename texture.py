from OpenGL.GL import *
import os.path
from PIL import Image
import numpy
from graphics import Graphics

class Texture:
    """Encapsulates the resources required to render a sprite with 
        an image mapped onto it. Keeps hold of the image data and the
        ID represetnation in OpenGL."""
    def __init__(self, texture_path: str):
        self.image = Image.open(texture_path)
        self.img_data = numpy.array(list(self.image.getdata()), numpy.uint8)
        self.texture_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.image.width, self.image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.img_data)

class Sprite():
    def __init__(self, graphics: Graphics, colour: list, pos: list, size: list):
        self.graphics = graphics
        self.pos = pos
        self.colour = colour
        self.size = size

    def set_alpha(self, new_alpha: float):
        self.colour[3] = new_alpha

class SpriteShape(Sprite):
    def __init__(self, graphics: Graphics, colour: list, pos: list, size: list):
        Sprite.__init__(self, graphics, colour, pos, size)

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

        self.vertex_pos_id = glGetAttribLocation(graphics.shader_colour, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)

        self.colour_id = glGetUniformLocation(graphics.shader_colour, "Colour")
        self.pos_id = glGetUniformLocation(graphics.shader_colour, "Position")
        self.size_id = glGetUniformLocation(graphics.shader_colour, "Size")

    def draw(self):
        glUseProgram(self.graphics.shader_colour)
        glUniform4f(self.colour_id, self.colour[0], self.colour[1], self.colour[2], self.colour[3]) 
        glUniform2f(self.pos_id, self.pos[0], self.pos[1]) 
        glUniform2f(self.size_id, self.size[0], self.size[1]) 
        glBindVertexArray(self.VAO)       
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT,  None)

class SpriteTexture(Sprite):
    def __init__(self, graphics: Graphics, tex: Texture, pos: tuple, size: tuple):
        Sprite.__init__(self, graphics, [1.0, 1.0, 1.0, 1.0], pos, size)
        self.texture = tex

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

        self.vertex_pos_id = glGetAttribLocation(graphics.shader_texture, "VertexPosition")
        glVertexAttribPointer(self.vertex_pos_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.vertex_pos_id)
 
        self.tex_coord_id = glGetAttribLocation(graphics.shader_texture, "TexCoord")
        glVertexAttribPointer(self.tex_coord_id, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(32))
        glEnableVertexAttribArray(self.tex_coord_id)

        self.colour_id = glGetUniformLocation(graphics.shader_texture, "Colour")
        self.pos_id = glGetUniformLocation(graphics.shader_texture, "Position")
        self.size_id = glGetUniformLocation(graphics.shader_texture, "Size")

    def draw(self):
        glUseProgram(self.graphics.shader_texture)
        glUniform4f(self.colour_id, self.colour[0], self.colour[1], self.colour[2], self.colour[3]) 
        glUniform2f(self.pos_id, self.pos[0], self.pos[1]) 
        glUniform2f(self.size_id, self.size[0], self.size[1]) 
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture.texture_id)
        glBindVertexArray(self.VAO)       
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT,  None)

class TextureManager:
    """The textures class handles loading and management of 
        all image resources for the game. The idea is that textures
        are loaded on demand and stay loaded until explicitly unloaded
        or the game is shutdown."""
    def __init__(self, base, graphics):
        self.base_path = base
        self.graphics = graphics
        self.textures = {}

    def get(self, texture_name: str) -> SpriteTexture:
        if texture_name in self.textures:
            return self.textures[texture_name]
        else:
            texture_path = os.path.join(self.base_path, texture_name)
            new_texture = Texture(texture_path)
            self.textures[texture_name] = new_texture
            return new_texture

    def create_sprite_shape(self, colour: list, position: list, size: list):
        return SpriteShape(self.graphics, colour, position, size)

    def create_sprite_texture(self, texture_name:str, position: tuple, size: tuple):
        return SpriteTexture(self.graphics, self.get(texture_name), position, size)

