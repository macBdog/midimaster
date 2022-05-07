from random import randrange
import numpy
from OpenGL.GL import *


class Particles:
    """Simple shader only particles for the entire game."""

    NumParticles = 256

    ComputeShader = """
    #version 430 core

    layout (local_size_x = 128, local_size_y = 2, local_size_z = 1) in;

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
        vec2 pos = positions[i];
        vec2 vel = velocities[i];
        float life = lifetimes[i];
        vec2 seed = vec2(i, i);

        life -= dt;

        pos += vel * dt;
        vel *= max(min(dt, 0.1), 0.0);

        if (life <= 0.0)
        {
            life = 1.0;
            pos = vec2(rand(vec2(1.0, 1.0)), rand(vec2(1.0, 1.0)));
            vel = vec2(rand(vec2(dt*10, dt*12)), rand(vec2(dt*13, dt*18)));
        }

        positions[i] = pos;
        velocities[i] = vel;
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
        Colour = vec4(1.0, 1.0, 1.0, Life);
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
        self.compute_shader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(Particles.ComputeShader, GL_COMPUTE_SHADER))

        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Particles.VertexShader, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Particles.PixelShader, GL_FRAGMENT_SHADER)
        )

        self.dt_id = glGetUniformLocation(self.compute_shader, "dt")

        self.position_buffer = glGenBuffers(1)
        self.positions = numpy.zeros(Particles.NumParticles * 2, dtype=numpy.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.position_buffer)
        glBufferData(GL_ARRAY_BUFFER, Particles.NumParticles * 4 * 2, self.positions, GL_DYNAMIC_COPY)

        self.velocities_buffer = glGenBuffers(1)
        self.velocities = numpy.zeros(Particles.NumParticles * 2, dtype=numpy.float32)

        self.lifetimes_buffer = glGenBuffers(1)
        self.lifetimes = numpy.ones(Particles.NumParticles, dtype=numpy.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.lifetimes_buffer)
        glBufferData(GL_ARRAY_BUFFER, Particles.NumParticles * 4, self.lifetimes, GL_DYNAMIC_COPY)

    def draw(self, dt: float):
        """Incovate the compute shader to mutate the positions and lifetime data,
        then use standard array drawing to render the particle quads."""

        glUseProgram(self.compute_shader)
        glUniform1f(self.dt_id, dt)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, self.position_buffer)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, self.lifetimes_buffer)
        glDispatchCompute(Particles.NumParticles // 128, 1, 1)
        glMemoryBarrier(GL_ALL_BARRIER_BITS)
        glUseProgram(0)

        glUseProgram(self.shader)
        # glUniform2f(self.size_id, 0.1, 0.1778)
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
