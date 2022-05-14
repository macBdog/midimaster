from settings import GameSettings
from graphics import Graphics
from OpenGL.GL import *

from texture import SpriteTexture, Texture


class Particles:
    """Simple shader only particles for the entire game."""

    NumEmitters = 8

    PIXEL_SHADER_PARTICLES = """
    #version 430

    in vec2 OutTexCoord;     
    uniform sampler2D SamplerTex;
    uniform vec4 Colour;
    out vec4 outColour;

    #define grav 0.1

    vec2 getPos(in vec2 o, in float t, in vec2 d) 
    {
        return vec2(o.x + d.x * t, o.y + d.y * t - grav * t * t);
    }

    vec3 drawParticle(in vec2 p, in float size, in vec3 col) 
    {
        return mix(col, vec3(0.0), smoothstep(0.0, size, dot(p, p) * 90.0));
    }

    void main() 
    {
        vec2 uv = OutTexCoord;
        uv.y /= 1.6667;

        vec4 rand = texture(SamplerTex, OutTexCoord) * Colour;

        vec3 col = vec3(0.0);
        col += drawParticle(uv, 2.0, vec3(0.1, 0.92, 0.02));
                
        outColour = vec4(col.xyz, 1.0) + (rand * 0.001);
    }
    """

    def __init__(self, graphics: Graphics):
        self.emitters = [0.0] * Particles.NumEmitters
        self.emitter_positions = [0.0] * Particles.NumEmitters * 2
        
        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_TEXTURE, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Particles.PIXEL_SHADER_PARTICLES, GL_FRAGMENT_SHADER)
        )

        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.dt_id = glGetUniformLocation(self.shader, "Dt")
        self.emitters_id = glGetUniformLocation(self.shader, "Emitters")
        self.emitter_positions_id = glGetUniformLocation(self.shader, "EmitterPositions")


    def spawn(self, num: int, speed: float, pos: list, colour: list, life: float = 1.0):
        """Create a bunch of particles at a location to be animated until they die."""

        emitter_id = -1
        for i, e in enumerate(self.emitters):
            if e <= 0.0:
                emitter_id = i
                self.emitters[i] = life
                break

        if emitter_id >= 0:
            epos_id = emitter_id * 2
            self.emitter_positions[epos_id] = pos[0]
            self.emitter_positions[epos_id + 1] = pos[1]
        elif GameSettings.DEV_MODE:
            print(f"Particle system has run out of emitters!")
            
    def draw(self, dt: float):
        """Uploade the emitters state to the shader every frame."""

        self.emitters = [x -dt for x in self.emitters]
        
        def particle_uniforms():
            glUniform1f(self.dt_id, dt)
            glUniform1fv(self.emitters_id, Particles.NumEmitters, self.emitters)
            glUniform2fv(self.emitter_positions_id, Particles.NumEmitters, self.emitter_positions)
        
        self.sprite.draw(None)

    def end(self):
        pass
