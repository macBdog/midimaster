import numpy
from pathlib import Path
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.constant import Constant

from settings import GameSettings

class Graphics:
    SHADER_PATH = "ext/shaders"

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

    PIXEL_SHADER_TEXTURE_SCROLL = """
    #version 430

    in vec2 OutTexCoord;     
    uniform sampler2D SamplerTex;
    uniform vec4 Colour;
    out vec4 outColour;

    float iTime = 0.0;

    void main() 
    {
        vec2 scroll = OutTexCoord + vec2(iTime, iTime);
        outColour = texture(SamplerTex, scroll) * Colour;
        iTime += 0.0015;
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

        # Pre-compile multiple shaders for general purpose drawing
        self.shader_texture = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_TEXTURE, GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(Graphics.PIXEL_SHADER_TEXTURE, GL_FRAGMENT_SHADER)
        )

        self.shader_colour = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_COLOUR, GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(Graphics.PIXEL_SHADER_COLOUR, GL_FRAGMENT_SHADER)
        )

        self.shader_font = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.VERTEX_SHADER_FONT, GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(Graphics.PIXEL_SHADER_FONT, GL_FRAGMENT_SHADER)
        )


    @staticmethod
    def compile_shader(vertex_shader_source: str, pixel_shader_source: str):
        return OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(vertex_shader_source, GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(pixel_shader_source, GL_FRAGMENT_SHADER)
        )

    @staticmethod
    def load_shader(name: str) -> str:
        path = Path(__file__).parent / Graphics.SHADER_PATH / name
        with open(path, 'r') as shader_file:
            return shader_file.read()

    @staticmethod
    def process_shader_source(src: str, subs: dict) -> str:
        for key, sub in subs.items():
            if src.find(key):
                src = src.replace(key, str(sub))
            elif GameSettings.DEV_MODE:
                print(f"Cannot find shader substitute key: {key} ")
        return src


    @staticmethod
    def print_all_uniforms(shader: int):
        num_uniforms = glGetProgramiv(shader, GL_ACTIVE_UNIFORMS)
        for i in range(num_uniforms):
            name, size, type = glGetActiveUniform(shader, i)
            print(f"Shader unfiform dump - Name: {name}, type: {type}, size: {size}")


    @staticmethod
    def debug_print_shader(vertex_source: str, fragment_source: str):
        """Utility function to compile and link a shader and print all log info out."""
        program = glCreateProgram()

        vshader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vshader, vertex_source)
        glCompileShader(vshader)
        glAttachShader(program, vshader)
        print(glGetShaderInfoLog(vshader))
        
        fshader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fshader, fragment_source)
        glCompileShader(fshader)
        glAttachShader(program, fshader)
        print(glGetShaderInfoLog(fshader))
        
        glLinkProgram(program)
        print(glGetProgramInfoLog(program))   
