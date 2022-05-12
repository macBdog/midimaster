from random import randrange
from settings import GameSettings
import numpy
from OpenGL.GL import *


class Particles:
    """Simple shader only particles for the entire game."""

    NumParticles = 512
    NumEmitters = 32

    ComputeShader = """
    #version 430 core

    layout (local_size_x = 512, local_size_y = 1, local_size_z = 1) in;

    layout (std430, binding = 0) buffer PositionBuffer {
        vec2 positions[];
    };
    layout (std430, binding = 0) buffer VelocityBuffer {
        vec2 velocities[];
    };
    layout (std430, binding = 1) buffer LifeBuffer {
        float lifetimes[];
    };

    uniform float dt;
    uniform float emitters[32];
    uniform vec2 emitter_positions[32];
    
    highp float rand(vec2 co)
    {
        highp float a = 12.9898;
        highp float b = 78.233;
        highp float c = 43758.5453;
        highp float dt= dot(co.xy ,vec2(a,b));
        highp float sn= mod(dt,3.14);
        return fract(sin(sn) * c);
    }

    void main(void)
    {
        uint i = gl_GlobalInvocationID.x;
        uint e = i % 32;
        vec2 pos = positions[i];
        vec2 vel = velocities[i];
        float life = lifetimes[i];

        life = max(0.0, life - dt) + emitters[e];
        if (life <= 0.0)
        {
            pos = vec2(-999.0, -999.0);
        }
        else
        {
            pos = vec2(0.0, 0.0);
        }

        pos += vec2(0.0, 0.0);

        positions[i] = emitter_positions[e] + pos;
        lifetimes[i] = life;
    }
    """

    VertexShader = """
    #version 430

    layout (location = 0) in vec2 VertexPosition;
    layout (location = 1) in float Life;

    out vec4 Colour;
    
    void main()
    {
        Colour = vec4(0.0, 1.0, 1.0, Life);
        gl_Position = vec4(VertexPosition.x, VertexPosition.y, 0.0, 1.0);
    }
    """

    PixelShader = """
    #version 430

    in vec4 Colour; 
    out vec4 Out;

    void main (void)
    {
        Out = Colour;
        //float dist = 1.0 - length((Vertex_UV * 2.0) - 1.0);
        //FragColor = vec4(Vertex_Color.x, Vertex_Color.y, Vertex_Color.z, dist);
    }
    """

    def __init__(self):
        self.emitters = [0.0] * Particles.NumEmitters
        self.emitter_positions = [0.0] * Particles.NumEmitters * 2

        self.compute_shader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(Particles.ComputeShader, GL_COMPUTE_SHADER))

        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Particles.VertexShader, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Particles.PixelShader, GL_FRAGMENT_SHADER)
        )

        self.dt_id = glGetUniformLocation(self.compute_shader, "dt")
        self.emitters_id = glGetUniformLocation(self.compute_shader, "emitters")
        self.emitter_positions_id = glGetUniformLocation(self.compute_shader, "emitter_positions")

        self.position_buffer = glGenBuffers(1)
        self.positions = numpy.zeros(Particles.NumParticles * 2, dtype=numpy.float32)

        for i in range(Particles.NumParticles * 2):
            if i % 2 == 0:
                self.positions[i] = i / 512

        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glBufferData(GL_ARRAY_BUFFER, Particles.NumParticles * 4 * 2, self.positions, GL_DYNAMIC_COPY)

        self.velocities_buffer = glGenBuffers(1)
        self.velocities = numpy.zeros(Particles.NumParticles * 2, dtype=numpy.float32)

        self.lifetimes_buffer = glGenBuffers(1)
        self.lifetimes = numpy.ones(Particles.NumParticles, dtype=numpy.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.lifetimes_buffer)
        glBufferData(GL_ARRAY_BUFFER, Particles.NumParticles * 4, self.lifetimes, GL_DYNAMIC_COPY)


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
        elif GameSettings.dev_mode:
            print(f"Particle system has run out of emitters!")
            
    def draw(self, dt: float):
        """Incovate the compute shader to mutate the positions and lifetime data,
        then use standard array drawing to render the particle quads."""

        glUseProgram(self.compute_shader)
        glUniform1f(self.dt_id, dt)
        glUniform1fv(self.emitters_id, Particles.NumEmitters, self.emitters)
        glUniform2fv(self.emitter_positions_id, Particles.NumEmitters, self.emitter_positions)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, self.position_buffer)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, self.velocities_buffer)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, self.lifetimes_buffer)
        glDispatchCompute(1, 1, 1)
        glMemoryBarrier(GL_ALL_BARRIER_BITS)
        glUseProgram(0)

        glUseProgram(self.shader)
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glBindBuffer(GL_ARRAY_BUFFER, self.lifetimes_buffer)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 4, ctypes.c_void_p(0))

        glDrawArrays(GL_POINTS, 0, Particles.NumParticles)

    def end(self):
        glDeleteBuffers(1, self.position_buffer)
        glDeleteBuffers(1, self.lifetimes_buffer)
