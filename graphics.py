from OpenGL.GL import *
import numpy

class Graphics():
    def __init__(self):

        self.rectangle = [  -0.5, -0.5, 0.0,        1.0, 1.0, 1.0,          0.0, 0.0,
                            0.5, -0.5, 0.0,         1.0, 1.0, 1.0,          1.0, 0.0,
                            0.5, 0.5, 0.0,          1.0, 1.0, 1.0,          1.0, 1.0,
                            -0.5, 0.5, 0.0,         1.0, 1.0, 1.0,          0.0, 1.0]

        self.rectangle = numpy.array(self.rectangle, dtype = numpy.float32)
        self.indices = numpy.array([0,1,2,2,3,0], dtype = numpy.uint32)

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
        # Create array object
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Create Buffer object in gpu
        self.VBO = glGenBuffers(1)

        # Bind the buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, 128, self.rectangle, GL_STATIC_DRAW) 

        # Create EBO
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

        self.position = glGetAttribLocation(self.shader, "position")
        glVertexAttribPointer(self.position, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        glEnableVertexAttribArray(self.position)

        self.colour = glGetAttribLocation(self.shader, "colour")
        glVertexAttribPointer(self.colour, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
        glEnableVertexAttribArray(self.colour)
 
        self.texCoords = glGetAttribLocation(self.shader, "texcoord")
        glVertexAttribPointer(self.texCoords, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(24))
        glEnableVertexAttribArray(self.texCoords)
