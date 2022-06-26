from graphics import Graphics
from OpenGL.GL import *
from texture import TextureManager
from graphics import Graphics

class ScrollingBackground:
    """Draw a texture that continuously scrolls."""

    def __init__(self, textures: TextureManager, texture: str):
        self.time = 0.0

        self.shader = Graphics.compile_shader(Graphics.load_shader("texture.vert"), Graphics.load_shader("texture_anim.frag"))
        self.time_id = glGetUniformLocation(self.shader, "Time")
        self.bg = textures.create_sprite_texture(texture, (0.0, 0.0), (2.0, 2.0), self.shader)
        
    def draw(self, dt):
        self.time += dt

        def anim_uniforms():
            glUniform1f(self.time_id, self.time)

        self.bg.draw(anim_uniforms)
