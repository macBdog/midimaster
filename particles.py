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
    out vec4 outColour;

    uniform sampler2D SamplerTex;
    uniform vec4 Colour;
    uniform float DisplayRatio;
    uniform float Emitters[NUM_PARTICLE_EMITTERS];
    uniform vec2 EmitterPositions[NUM_PARTICLE_EMITTERS];
    uniform vec3 EmitterColours[NUM_PARTICLE_EMITTERS];
    
    #define num_particles 32
    #define grav -0.25
    #define psize 0.05

    float rand(vec2 c) 
    {
        return fract(sin(dot(c.xy , vec2(12.9898, 78.233))) * 43758.5453);
    }

    vec2 noise(vec2 tc)
    {
        return (2.0 * texture(SamplerTex, tc).xy - 1.).xy;
    }

    vec2 getPos(in vec2 o, in float time, in vec2 dir) 
    {
        return vec2(o.x + dir.x * time, o.y + dir.y * time - grav * time * time);
    }

    vec4 drawParticle(in vec2 pos, in float size, in vec4 col) 
    {
        return mix(col, vec4(0.0), smoothstep(0.0, size, dot(pos, pos) * 90.0));
    }

    void main() 
    {
        vec2 uv = OutTexCoord;
        uv.y *= DisplayRatio;
        vec4 screen_col = vec4(0.0);

        for (int e = 0; e < NUM_PARTICLE_EMITTERS; ++e)
        {
            float life = max(Emitters[e], 0.0);
            vec2 pos = EmitterPositions[e] * vec2(0.5, DisplayRatio);
            vec3 col = EmitterColours[e];

            col = vec3(0.11, 0.85, 0.02);

            for (int i = 0; i < num_particles; ++i)
            {
                float c = float(i) / float(num_particles);
                vec2 rdir = noise(vec2(sin(c), cos(c))) * 0.5;
                vec2 pos = getPos(pos, 1.0 - life, rdir);
                screen_col += drawParticle(uv - pos, psize, vec4(col.xyz, life));
            }
        }
                
        outColour = screen_col;
    }
    """.replace("NUM_PARTICLE_EMITTERS", str(NumEmitters))

    def __init__(self, graphics: Graphics, display_ratio: float):
        self.display_ratio = 1.0 / display_ratio
        self.emitter = -1
        self.emitters = [0.0] * Particles.NumEmitters
        self.emitter_positions = [0.0] * Particles.NumEmitters * 2
        self.emitter_colours = [0.0] * Particles.NumEmitters * 3
        
        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_TEXTURE, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Particles.PIXEL_SHADER_PARTICLES, GL_FRAGMENT_SHADER)
        )

        self.texture = Texture("")
        self.sprite = SpriteTexture(graphics, self.texture, [1.0, 1.0, 1.0, 1.0], [0.0, 0.0], [2.0, 2.0], self.shader)

        self.display_ratio_id = glGetUniformLocation(self.shader, "DisplayRatio")
        self.emitters_id = glGetUniformLocation(self.shader, "Emitters")
        self.emitter_positions_id = glGetUniformLocation(self.shader, "EmitterPositions")
        self.emitter_colours_id = glGetUniformLocation(self.shader, "EmitterColours")


    def spawn(self, num: int, speed: float, pos: list, colour: list, life: float = 1.0):
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
        epos_id = self.emitter * 2
        self.emitter_positions[epos_id] = pos[0]
        self.emitter_positions[epos_id + 1] = pos[1]

        self.emitter_positions[epos_id] = 0.5
        self.emitter_positions[epos_id + 1] = 0.5

        ecol_id = self.emitter * 3
        self.emitter_colours[ecol_id] * colour[0]
        self.emitter_colours[ecol_id + 1] * colour[1]
        self.emitter_colours[ecol_id + 2] * colour[2]
            
    def draw(self, dt: float):
        """Upload the emitters state to the shader every frame."""

        self.emitters = [x -dt for x in self.emitters]
        
        def particle_uniforms():
            glUniform1f(self.display_ratio_id, self.display_ratio)
            glUniform1fv(self.emitters_id, Particles.NumEmitters, self.emitters)
            glUniform2fv(self.emitter_positions_id, Particles.NumEmitters, self.emitter_positions)
            glUniform3fv(self.emitter_colours_id, Particles.NumEmitters, self.emitter_colours)
        
        self.sprite.draw(particle_uniforms)

    def end(self):
        pass
