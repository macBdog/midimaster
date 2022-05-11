import glfw
from graphics import Graphics
from input import Input, InputActionKey, InputMethod, InputActionModifier
from texture import *
import time
from gui import Gui
from profile import Profile
from particles import Particles
from settings import GameSettings

class Game:
    """A generic interactive frame interpolation loop without connection to specific logic."""

    def __init__(self):
        self.name = "game"
        self.running = False
        self.window_width = 1280
        self.window_height = 720
        self.dt = 0.03
        self.fps = 0
        self.fps_last_update = 1

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
        self.particles = Particles()
        self.profile = Profile()

        self.input.add_key_mapping(256, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.end)
        self.input.add_key_mapping(283, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, self.profile.capture_next_frame)

        glViewport(0, 0, self.window_width, self.window_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
        glfw.swap_interval(GameSettings.VSYNC)

        self.gui = Gui(self.window_width, self.window_height, "gui")
        self.gui.set_active(False, False)

    def begin(self):
        dt_cur = dt_last = time.time()

        while self.running and not glfw.window_should_close(self.window):
            self.profile.update()

            dt_cur = time.time()
            self.dt = dt_cur - dt_last
            dt_last = dt_cur
            self.fps_last_update -= self.dt

            if self.fps_last_update <= 0:
                self.fps = 1.0 / self.dt
                self.fps_last_update = 1.0

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            self.profile.begin("gui")
            self.gui.touch(self.input.cursor)
            self.gui.draw(self.dt)
            self.profile.end()

            self.profile.begin("particles")
            self.particles.draw(self.dt)
            self.profile.end()

            self.update(self.dt)

            glfw.swap_buffers(self.window)
            glfw.poll_events()
        self.end()

    def update(self, dt):
        # Child classes define frame specific behaviour here
        pass

    def end(self):
        self.running = False
        glfw.terminate()
