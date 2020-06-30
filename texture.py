from OpenGL.GL import *
import os.path
from PIL import Image
import numpy

class SpriteShape():
    def __init__(self, pos: tuple, size: tuple, colour: tuple):
        self.pos = pos
        self.size = size
        self.colour = colour

    def draw(self):
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT,  None)

class SpriteTexture(SpriteShape):
    def __init__(self, texture_path: str):
        SpriteShape.__init__(self, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.,0))
        self.texture = Texture(texture_path)

    def draw(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture.texture_id)
        super().draw()

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
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.image.width, self.image.height, 0, GL_RGB, GL_UNSIGNED_BYTE, self.img_data)

class TextureManager:
    """The textures class handles loading and management of 
        all image resources for the game. The idea is that textures
        are loaded on demand and stay loaded until explicitly unloaded
        or the game is shutdown."""
    def __init__(self, base, subsystems):
        self.base_path = base
        self.sub_paths = []
        self.sub_paths += subsystems

    def get(self, texture_name: str) -> SpriteTexture:
        texture_path = os.path.join(self.base_path, texture_name)
        return Texture(texture_path)

    def get_sub(self, sub_name: str, texture_name:str) -> SpriteTexture:
        if sub_name in self.sub_paths:
            texture_path = os.path.join(sub_name, texture_name)
            return self.get(texture_path)
