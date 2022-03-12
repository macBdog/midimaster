import glfw
from graphics import Graphics
from input import Input, InputMethod
from texture import *
import time

# Dependency list:
# numpy, Pillow, glfw, PyOpenGL, PyOpenGL_accelerate, mido, freetype-py, python-rtmidi

class Game:
    """ A generic interactive frame interpolation loop without connection to specific logic."""

    def __init__(self):
        self.name = "game"
        self.running = False
        self.dev_mode = True
        self.window_width = 1280
        self.window_height = 720
        self.dt = 0.03
        self.fps = 0
        self.fps_last_update = 0
        
    def prepare(self, texture_path: str = "tex"):
        if not glfw.init():
            return
    
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(self.window_width, self.window_height, self.name, None, None)
    
        if not self.window:
            glfw.terminate()
            return
    
        glfw.make_context_current(self.window)
        
        self.running = True

        # Now we have an OpenGL context we can compile GPU programs
        self.graphics = Graphics()
        self.textures = TextureManager(texture_path, self.graphics)
        self.input = Input(self.window, InputMethod.KEYBOARD)

        glViewport(0, 0, self.window_width, self.window_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)    
        glShadeModel(GL_SMOOTH) 
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glfw.swap_interval(1)        

    def begin(self):
        dt_cur = dt_last = time.time()

        while self.running and not glfw.window_should_close(self.window):
            glfw.poll_events()

            dt_cur = time.time()
            self.dt = dt_cur - dt_last
            dt_last = dt_cur
            self.fps_last_update -= self.dt

            if self.fps_last_update <= 0:
                self.fps = 1.0 / self.dt
                self.fps_last_update = 1.0

            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

            self.update(self.dt)

            glfw.swap_buffers(self.window)
        self.end()
    
    def update(self, dt):
        # Child classes define frame specific behaviour here
        pass

    def end(self):
        glfw.terminate()

            