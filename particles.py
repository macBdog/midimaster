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
    uniform float Emitters[8];
    uniform vec2 EmitterPositions[8];
    out vec4 outColour;

    #define grav 0.1
    #define psize 0.35

    float rand(vec2 c) 
    {
        return fract(sin(dot(c.xy , vec2(12.9898, 78.233))) * 43758.5453);
    }

    float randDir(float val, float seed) 
    {
        return cos(val * sin(val * seed) * seed);
    }

    float hash(in float n ) 
    {
        return fract(sin(n) * 43758.5453123);
    }

    vec2 getPos(in vec2 o, in float t, in vec2 d) 
    {
        return vec2(o.x + d.x * t, o.y + d.y * t - grav * t * t);
    }

    vec4 drawParticle(in vec2 p, in float size, in vec4 col) 
    {
        return mix(col, vec4(0.0), smoothstep(0.0, size, dot(p, p) * 90.0));
    }

    void main() 
    {
        vec2 uv = OutTexCoord;
        uv.y /= 1.6667;

        float life = Emitters[0];

        float range = (sin(life * 2.0) + 1.0) * 0.5; 
        vec2 pos = vec2(range, 0.250);

        vec4 rand = texture(SamplerTex, OutTexCoord) * Colour;

        vec4 col = vec4(0.0);
        col += drawParticle(uv - pos, psize, vec4(0.1, 0.92, 0.02, max(life, 0.25)));
                
        outColour = col + (rand * 0.001);
    }
    """

    def __init__(self, graphics: Graphics):
        self.emitters = [1.0] * Particles.NumEmitters
        self.emitter_positions = [0.0] * Particles.NumEmitters * 2
        
        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_TEXTURE, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Particles.PIXEL_SHADER_PARTICLES, GL_FRAGMENT_SHADER)
        )

        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        graphics.print_all_uniforms(self.shader)

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
        """Upload the emitters state to the shader every frame."""

        self.emitters = [x -dt for x in self.emitters]
        
        def particle_uniforms():
            glUniform1fv(self.emitters_id, Particles.NumEmitters, self.emitters)
            glUniform2fv(self.emitter_positions_id, Particles.NumEmitters, self.emitter_positions)
        
        self.sprite.draw(particle_uniforms)

    def end(self):
        pass
