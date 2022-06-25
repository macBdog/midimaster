import numpy
from pathlib import Path
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.constant import Constant

from settings import GameSettings

class Graphics:
    SHADER_PATH = "ext/shaders"

    def __init__(self):
        self.indices = numpy.array([0, 1, 2, 2, 3, 0], dtype=numpy.uint32)

        # Pre-compile multiple shaders for general purpose drawing
        self.shader_texture = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.load_shader("texture.vert"), GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(Graphics.load_shader("texture.frag"), GL_FRAGMENT_SHADER)
        )

        self.shader_colour = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.load_shader("colour.vert"), GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(Graphics.load_shader("colour.frag"), GL_FRAGMENT_SHADER)
        )

        self.shader_font = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(Graphics.load_shader("font.vert"), GL_VERTEX_SHADER), 
            OpenGL.GL.shaders.compileShader(Graphics.load_shader("font.frag"), GL_FRAGMENT_SHADER)
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
