import numpy
from OpenGL.GL import *
from OpenGL.GL import shaders

class Graphics:
    VERTEX_SHADER_TEXTURE = """
    #version 430

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

    PIXEL_SHADER_TEXTURE = """
    #version 430

    in vec2 OutTexCoord;     
    uniform sampler2D SamplerTex;
    uniform vec4 Colour;
    out vec4 outColour;

    void main() 
    {
        outColour = texture(SamplerTex, OutTexCoord) * Colour;
    }
    """

    VERTEX_SHADER_COLOUR = """
    #version 430

    in vec2 VertexPosition;
    uniform vec2 Position;
    uniform vec2 Size;

    void main() 
    {
        gl_Position = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
    }
    """

    PIXEL_SHADER_COLOUR = """
    #version 430

    uniform vec4 Colour;
    out vec4 outColour;

    void main() 
    {
        outColour = Colour;
    }
    """

    VERTEX_SHADER_FONT = """
    #version 430

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

    PIXEL_SHADER_FONT = """
    #version 430

    in vec2 OutTexCoord;     
    uniform sampler2D SamplerTex;
    uniform vec4 Colour;
    out vec4 outColour;

    void main() 
    {
        vec4 char_col = Colour;
        char_col.a = texture(SamplerTex, OutTexCoord).r;
        outColour = char_col;
    }
    """

    def __init__(self):
        self.indices = numpy.array([0, 1, 2, 2, 3, 0], dtype=numpy.uint32)

        # Compile multiple shaders for different purposes
        self.shader_texture = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_TEXTURE, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Graphics.PIXEL_SHADER_TEXTURE, GL_FRAGMENT_SHADER)
        )

        self.shader_colour = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_COLOUR, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Graphics.PIXEL_SHADER_COLOUR, GL_FRAGMENT_SHADER)
        )

        self.shader_font = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_FONT, GL_VERTEX_SHADER), OpenGL.GL.shaders.compileShader(Graphics.PIXEL_SHADER_FONT, GL_FRAGMENT_SHADER)
        )
