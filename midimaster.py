import pygame
import pygame.freetype
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL.GL.shaders
from texture import *
from gui import Gui
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType
from music import Music
from mido import Message
from midi_devices import MidiDevices
from collections import deque 
from sprite_string import SpriteString
from texture import SpriteShape
from graphics import Graphics
import time
import math
import os.path

def main():
    """The entry point and controlling loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    window_width = 1280
    window_height = 720
    window_ratio = window_width / window_height
    
    pygame.init()

    if not glfw.init():
        return
 
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(window_width, window_height, "MidiMaster", None, None)
 
    if not window:
        glfw.terminate()
        return
 
    glfw.make_context_current(window)
    
    graphics = Graphics()
    textures = TextureManager("tex", graphics)

    font_game_path = os.path.join("ext", "BlackMetalSans.ttf")
    font_music_path = os.path.join("ext", "Musisync.ttf")

    # Create the holder UI for the game play elements
    gui_game = Gui(window_width, window_height)

    game_bg = textures.create_sprite("game_background.tga", (0.0, 0.0), (1.0, 1.0))
    gui_game.add_widget(game_bg)

    bg_score = gui_game.add_widget(textures.create_sprite("score_bg.tga", (0.0, -0.5), (0.25, 0.125)))
    bg_score.align(AlignX.Centre, AlignY.Bottom)

    running = True 

    testSprite = textures.create_sprite("particle_lightning.tga", (-0.2, 0.5), (0.25, 0.25))

    # Connect midi inputs and outputs
    devices = MidiDevices()
    devices.open_input_default()
    devices.open_output_default()

    glViewport(0, 0, window_width, window_height);
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glfw.swap_interval(1);

    music_time = 0.0
    music_running = True
    dt_cur = time.time()
    dt_last = time.time()
    midi_notes = {}
    while running and not glfw.window_should_close(window):
        glfw.poll_events()

        dt_cur = time.time()
        dt = dt_cur - dt_last
        dt_last = dt_cur
        
        devices.update()

        # Handle all events from MIDI input devices
        for message in devices.input_messages:
            if message.type == 'note_on' or message.type == 'note_off':
                score += 100
                score_id = message.note - staff_pitch_origin
                if score_id >= 0 and score_id < num_notes:
                    score_highlight[score_id] = 1.0
                devices.output_messages.append(message)

        devices.input_messages = []

        # Handle all events from pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key >= pygame.K_a and event.key <= pygame.K_g:
                    key_note_value = event.key - pygame.K_c
                    if key_note_value < 0:
                        key_note_value += 6
                    score_highlight[key_note_value] = 1.0
                    new_note = Message('note_on')
                    new_note.note = key_note_value + staff_pitch_origin
                    new_note.velocity = 100
                    devices.output_messages.append(new_note)
                elif event.key == pygame.K_p:
                    music_running = not music_running

        music_notes = {}
        
        # music_notes = music.draw(music_time)

        if music_running:
            music_time += dt * 120.0

        # Process all notes that have hit the play head
        music_notes_off = {}
        for k in music_notes:
            # Highlight the note box to show this note should be currently played
            if music_notes[k] >= music_time:
                highlight_id = k - staff_pitch_origin
                note_highlight[highlight_id] = 1.0

            # The note value in the dictionary is the time to turn off
            if k in midi_notes:
                if music_notes[k] < music_time:
                    music_notes_off[k] = True
            elif music_notes[k] >= music_time:   
                midi_notes[k] = music_notes[k]
                new_note_on = Message('note_on')
                new_note_on.note = k
                new_note_on.velocity = 100
                devices.output_messages.append(new_note_on)       


        # Send note off messages for all the notes in the music
        for k in music_notes_off:
            new_note_off = Message('note_off')
            new_note_off.note = k
            devices.output_messages.append(new_note_off)
            midi_notes.pop(k)

        # Pull the scoring box alpha down to 0
        # for i in range(num_notes):
            #note_box[i].texture.set_alpha(note_highlight[i] * 255)
            #if note_highlight[i] > note_base_alpha:
            #    note_highlight[i] -= 2.0 * dt

        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        glUseProgram(graphics.shader)

        gui_game.draw(dt)

        testSprite.draw()

        glfw.swap_buffers(window)

    devices.quit()
    pygame.quit()
    glfw.terminate()
main()
