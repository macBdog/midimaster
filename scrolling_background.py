from gamejam.graphics import Graphics
from OpenGL.GL import glUniform1f, glGetUniformLocation
from gamejam.texture import TextureManager
from gamejam.graphics import Graphics, Shader, ShaderType

class ScrollingBackground:
    """Draw a texture that continuously scrolls."""

    def __init__(self, graphics: Graphics, textures: TextureManager, texture: str):
        self.time = 0.0
        self.shader = graphics.get_program(Shader.ANIM)
        self.time_id = glGetUniformLocation(self.shader, "Time")
        self.bg = textures.create_sprite_texture(texture, [0, 0], [2, 2], self.shader)
        
    def draw(self, dt):
        self.time += dt

        def anim_uniforms():
            glUniform1f(self.time_id, self.time)

        self.bg.draw(anim_uniforms)
