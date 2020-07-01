from OpenGL.GL import *
import numpy

class Graphics():
    def __init__(self):

        vertex_shader_texture = """
        #version 330
 
        in vec3 position;
        in vec4 colour;
        in vec2 texcoord;
           
        out vec4 newColour;
        out vec2 OutTexCoords;
 
        void main() 
        {
            gl_Position = vec4(position, 1.0);
            newColour = colour;
            OutTexCoords = texcoord;
        }
        """

        pixel_shader_texture = """
        #version 330
 
        in vec4 newColour;
        in vec2 OutTexCoords;
         
        out vec4 outColour;
        uniform sampler2D samplerTex;
 
        void main() 
        {
           outColour = texture(samplerTex, OutTexCoords) * newColour;
        }
        """

        vertex_shader_colour = """
        #version 330
 
        in vec3 position;
        in vec4 colour;
           
        out vec4 newColour;
 
        void main() 
        {
            gl_Position = vec4(position, 1.0);
            newColour = colour;
        }
        """

        pixel_shader_colour = """
        #version 330
 
        in vec4 newColour;
         
        out vec4 outColour;
 
        void main() 
        {
           outColour = newColour;
        }
        """

        # Compile multiple shaders for different purposes
        self.shader_texture = OpenGL.GL.shaders.compileProgram( OpenGL.GL.shaders.compileShader(vertex_shader_texture, GL_VERTEX_SHADER),
                                                                OpenGL.GL.shaders.compileShader(pixel_shader_texture, GL_FRAGMENT_SHADER))

        self.shader_colour = OpenGL.GL.shaders.compileProgram( OpenGL.GL.shaders.compileShader(vertex_shader_colour, GL_VERTEX_SHADER),
                                                        OpenGL.GL.shaders.compileShader(pixel_shader_colour, GL_FRAGMENT_SHADER))

