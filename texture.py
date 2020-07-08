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

class SpriteShape():
    def __init__(self, graphics: Graphics, colour: tuple, pos: tuple, size: tuple):
        self.graphics = graphics
        self.pos = pos

        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)

        self.rectangle = [  pos[0]-size[0], pos[1]-size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],
                            pos[0]+size[0], pos[1]-size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],
                            pos[0]+size[0], pos[1]+size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],
                            pos[0]-size[0], pos[1]+size[1], 0.0,        colour[0], colour[1], colour[2], colour[3]]

        self.rectangle = numpy.array(self.rectangle, dtype = numpy.float32)
        self.indices = numpy.array([0,1,2,2,3,0], dtype = numpy.uint32)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 112, self.rectangle, GL_STATIC_DRAW) 

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

        self.position = glGetAttribLocation(graphics.shader_colour, "position")
        glVertexAttribPointer(self.position, 3, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.position)

        self.colour = glGetAttribLocation(graphics.shader_colour, "colour")
        glVertexAttribPointer(self.colour, 4, GL_FLOAT, GL_FALSE, 28, ctypes.c_void_p(12))
        glEnableVertexAttribArray(self.colour)

    def set_alpha(self, new_alpha: float):
        self.rectangle[6] = new_alpha
        self.rectangle[13] = new_alpha
        self.rectangle[20] = new_alpha
        self.rectangle[27] = new_alpha

    def draw(self):
        glUseProgram(self.graphics.shader_colour)
        glBindVertexArray(self.VAO)       
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT,  None)

class SpriteTexture(SpriteShape):
    def __init__(self, graphics: Graphics, tex: Texture, pos: tuple, size: tuple):
        colour = (1.0, 1.0, 1.0, 1.0)
        self.graphics = graphics
        self.texture = tex
        self.pos = pos

        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)

        self.rectangle = [  pos[0]-size[0], pos[1]-size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],     0.0, 1.0,
                            pos[0]+size[0], pos[1]-size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],     1.0, 1.0,
                            pos[0]+size[0], pos[1]+size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],     1.0, 0.0,
                            pos[0]-size[0], pos[1]+size[1], 0.0,        colour[0], colour[1], colour[2], colour[3],     0.0, 0.0]

        self.rectangle = numpy.array(self.rectangle, dtype = numpy.float32)
        self.indices = numpy.array([0,1,2,2,3,0], dtype = numpy.uint32)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 144, self.rectangle, GL_STATIC_DRAW) 

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

        self.position = glGetAttribLocation(graphics.shader_texture, "position")
        glVertexAttribPointer(self.position, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.position)

        self.colour = glGetAttribLocation(graphics.shader_texture, "colour")
        glVertexAttribPointer(self.colour, 4, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))
        glEnableVertexAttribArray(self.colour)
 
        self.texCoords = glGetAttribLocation(graphics.shader_texture, "texcoord")
        glVertexAttribPointer(self.texCoords, 2, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(28))
        glEnableVertexAttribArray(self.texCoords)

    def draw(self):
        glUseProgram(self.graphics.shader_texture)
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

    def create_sprite_shape(self, colour: tuple, position: tuple, size: tuple):
        return SpriteShape(self.graphics, colour, position, size)

    def create_sprite_texture(self, texture_name:str, position: tuple, size: tuple):
        return SpriteTexture(self.graphics, self.get(texture_name), position, size)

