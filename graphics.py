from OpenGL.GL import *
import numpy

class Graphics():
    def __init__(self):

        VERTEX_SHADER = """
        #version 330
 
        in vec3 position;
        in vec3 colour;
        in vec2 texcoord;
           
        out vec3 newColour;
        out vec2 OutTexCoords;
 
        void main() 
        {
            gl_Position = vec4(position, 1.0);
            newColour = colour;
            OutTexCoords = texcoord;
        }
        """

        FRAGMENT_SHADER = """
        #version 330
 
        in vec3 newColour;
        in vec2 OutTexCoords;
         
        out vec4 outColour;
        uniform sampler2D samplerTex;
 
        void main() 
        {
           outColour = texture(samplerTex, OutTexCoords) * vec4(newColour, 1.0);
        }
        """

        # Compile The Program and shaders
        self.shader = OpenGL.GL.shaders.compileProgram( OpenGL.GL.shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
                                                        OpenGL.GL.shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER))

