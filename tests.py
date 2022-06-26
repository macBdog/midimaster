import pygame
from font import Font
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from texture import TextureManager
from graphics import Graphics

def main():
    window_width = 1024
    window_height = 1024
    window_ratio = window_width / window_height
    
    pygame.init()

    if not glfw.init():
        return
 
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(window_width, window_height, "MidiMaster - Test", None, None)
 
    if not window:
        glfw.terminate()
        return
 
    glfw.make_context_current(window)

    graphics = Graphics()
    textures = TextureManager("tex", graphics)

    font_game_path = os.path.join("ext", "BlackMetalSans.ttf")
    font_game = Font(font_game_path, graphics, 12)

    glViewport(0, 0, window_width, window_height)
    glClearColor(0.25, 0.25, 0.25, 1.0)    
    glShadeModel(GL_SMOOTH) 
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glfw.swap_interval(1)

    running = True

    while running and not glfw.window_should_close(window):
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        font_game.draw("A test string", [0, 0], [1.0, 1.0, 1.0, 1.0])
        glfw.swap_buffers(window)

    pygame.quit()
    glfw.terminate()
main()
