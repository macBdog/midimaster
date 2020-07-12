from OpenGL.GL import *
import numpy

class Graphics():
    def __init__(self):
        self.indices = numpy.array([0,1,2,2,3,0], dtype = numpy.uint32)

        vertex_shader_texture = """
        #version 330
 
        in vec2 VertexPosition;
        in vec2 TexCoord;
        uniform vec2 Position;
        uniform vec2 Size;
        out vec2 OutTexCoord;

        void main() 
        {
            gl_Position = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
            OutTexCoord = TexCoord;
        }
        """

        pixel_shader_texture = """
        #version 330
 
        in vec2 OutTexCoord;     
        uniform sampler2D SamplerTex;
        uniform vec4 Colour;
        out vec4 outColour;
 
        void main() 
        {
           outColour = texture(SamplerTex, OutTexCoord) * Colour;
        }
        """

        vertex_shader_colour = """
        #version 330
 
        in vec2 VertexPosition;
        uniform vec2 Position;
        uniform vec2 Size;
 
        void main() 
        {
            gl_Position = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
        }
        """

        pixel_shader_colour = """
        #version 330
 
        uniform vec4 Colour;
        out vec4 outColour;
 
        void main() 
        {
           outColour = Colour;
        }
        """

        vertex_shader_font = """
        #version 330
 
        in vec2 VertexPosition;
        in vec2 TexCoord;
        uniform vec2 Position;
        uniform vec2 Size;
        out vec2 OutTexCoord;
        uniform vec2 CharCoord;
        uniform vec2 CharSize;

        void main() 
        {
            gl_Position = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
            OutTexCoord = vec2(CharCoord.x + TexCoord.x * CharSize.x, CharCoord.y + TexCoord.y * CharSize.y);
        }
        """

        pixel_shader_font = """
        #version 330
 
        in vec2 OutTexCoord;     
        uniform sampler2D SamplerTex;
        uniform vec4 Colour;
        out vec4 outColour;
 
        void main() 
        {
           outColour = texture(SamplerTex, OutTexCoord) * Colour;
        }
        """

        # Compile multiple shaders for different purposes
        self.shader_texture = OpenGL.GL.shaders.compileProgram( OpenGL.GL.shaders.compileShader(vertex_shader_texture, GL_VERTEX_SHADER),
                                                                OpenGL.GL.shaders.compileShader(pixel_shader_texture, GL_FRAGMENT_SHADER))

        self.shader_colour = OpenGL.GL.shaders.compileProgram( OpenGL.GL.shaders.compileShader(vertex_shader_colour, GL_VERTEX_SHADER),
                                                        OpenGL.GL.shaders.compileShader(pixel_shader_colour, GL_FRAGMENT_SHADER))

        self.shader_font = OpenGL.GL.shaders.compileProgram( OpenGL.GL.shaders.compileShader(vertex_shader_font, GL_VERTEX_SHADER),
                                                                OpenGL.GL.shaders.compileShader(pixel_shader_font, GL_FRAGMENT_SHADER))

