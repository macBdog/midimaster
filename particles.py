from settings import GameSettings
from graphics import Graphics
from texture import SpriteTexture, Texture

from OpenGL.GL import (
    glGetUniformLocation,
    glUniform1f,
    glUniform1fv,
    glUniform2fv,
    glUniform3fv
)

class Particles:
    """Simple shader only particles for the entire game."""
    NumEmitters = 8

    def __init__(self, graphics: Graphics, display_ratio: float):
        self.display_ratio = 1.0 / display_ratio
        self.emitter = -1
        self.emitters = [0.0] * Particles.NumEmitters
        self.emitter_speeds = [1.0] * Particles.NumEmitters
        self.emitter_positions = [0.0] * Particles.NumEmitters * 2
        self.emitter_colours = [0.0] * Particles.NumEmitters * 3
        
        shader_substitutes = {
            "NUM_PARTICLE_EMITTERS": str(Particles.NumEmitters)
        }
        particle_shader = Graphics.process_shader_source(Graphics.load_shader("particles.frag"), shader_substitutes)
        self.shader = Graphics.compile_shader(Graphics.load_shader("texture.vert"), particle_shader)
        
        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.emitters_id = glGetUniformLocation(self.shader, "Emitters")
        self.emitter_positions_id = glGetUniformLocation(self.shader, "EmitterPositions")
        self.emitter_colours_id = glGetUniformLocation(self.shader, "EmitterColours")


    def spawn(self, speed: float, pos: list, colour: list, life: float = 1.0):
        """Create a bunch of particles at a location to be animated until they die."""

        search = 0
        new_emitter = (self.emitter + 1) % Particles.NumEmitters
        while self.emitters[new_emitter] > 0.0:
            search += 1
            new_emitter = (self.emitter + search) % Particles.NumEmitters
            if search >= Particles.NumEmitters:
                if GameSettings.DEV_MODE:
                    print(f"Particle system has run out of emitters!")
                break
        
        self.emitter = new_emitter
        self.emitters[self.emitter] = life
        self.emitter_speeds[self.emitter] = speed

        epos_id = self.emitter * 2
        self.emitter_positions[epos_id] = pos[0]
        self.emitter_positions[epos_id + 1] = pos[1]

        ecol_id = self.emitter * 3
        self.emitter_colours[ecol_id] = colour[0]
        self.emitter_colours[ecol_id + 1] = colour[1]
        self.emitter_colours[ecol_id + 2] = colour[2]
            
    def draw(self, dt: float):
        """Upload the emitters state to the shader every frame."""

        self.emitters = [x - (dt * self.emitter_speeds[i]) for i, x in enumerate(self.emitters)]
        
        def particle_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform1fv(self.emitters_id, Particles.NumEmitters, self.emitters)
            glUniform2fv(self.emitter_positions_id, Particles.NumEmitters, self.emitter_positions)
            glUniform3fv(self.emitter_colours_id, Particles.NumEmitters, self.emitter_colours)
        
        self.sprite.draw(particle_uniforms)

    def end(self):
        pass
