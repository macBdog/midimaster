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
from font import Font
from texture import SpriteShape
from graphics import Graphics
import time
import math
import os.path

# Dependency list:
# numpy, Pillow, pygame, OpenGL, mido, freetype-py, python-rtmidi

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
    
    running = True 

    graphics = Graphics()
    textures = TextureManager("tex", graphics)

    font_game_path = os.path.join("ext", "BlackMetalSans.ttf")
    font_music_path = os.path.join("ext", "Musisync.ttf")
    font_game_h1 = Font(font_game_path, graphics, 24)
    font_game_h2 = Font(font_game_path, graphics, 24)
    font_game_body = Font(font_game_path, graphics, 24)
    font_game_music_large = Font(font_music_path, graphics, 24)

    show_intro = False

    if show_intro:
        # Create a background image stretched to the size of the window
        gui_splash = Gui(screen, sprites, window_width, window_height)
        bg_splash = gui_splash.add_widget(textures.get("menu_background.tga"), 0, 0)

        # Create a title image and fade it in
        title = gui_splash.add_widget(textures.get_sub("gui", "imgtitle.tga"), gui_splash.width / 2, gui_splash.height / 2)
        title.animation = Animation(AnimType.FadeIn, 0.25)

    # Create the holder UI for the game play elements
    gui_game = Gui(window_width, window_height)

    game_bg = textures.create_sprite_texture("game_background.tga", (0.0, 0.0), (2.0, 2.0))
    gui_game.add_widget(game_bg)

    bg_score = gui_game.add_widget(textures.create_sprite_texture("score_bg.tga", (0.0, -0.75), (0.5, 0.25)))
    bg_score.align(AlignX.Centre, AlignY.Bottom)

    # Draw the 12 note lines with the staff lines of the treble clef highlighted
    staff_pos_x = 0.15
    staff_pos_y = 0.0
    staff_width = 1.85
    staff_lines = []
    note_spacing = 0.085
    staff_spacing = note_spacing * 2
    note_base_alpha = 0.25
    score_base_alpha = 0.33
    num_staff_lines = 4
    staff_pitch_origin = 60 # Using middle C4 as the reference note
    incidentals = {1: True, 3: True, 6: True, 8: True, 10: True, 13: True, 15: True, 18: True, 20: True}
    note_colours = [[0.98, 0.25, 0.22, 1.0], [1.0, 0.33, 0.30, 1.0], [0.78, 0.55, 0.99, 1.0], [0.89, 173, 255, 1.0], [1.0, 0.89, 63, 1.0], [0.39, 0.39, 0.55, 1.0], [0.47, 0.47, 0.67, 1.0],  # C4, Db4, D4, Eb4, E4, F4, Gb4
                    [0.89, 0.97, 1.0, 1.0], [0.95, 1.0, 1.0, 1.0], [0.67, 0.1, 0.01, 1.0], [0.78, 0.18, 0.09, 1.0], [0, 0.78, 1.0, 1.0], [1.0, 0.39, 1, 1.0], [1.0, 0.47, 0.1, 1.0],       # G4, Ab4, A4, Bb4, B4, C5, Db5
                    [1.0, 0.375, 0.89, 1.0], [1.0, 0.48, 1.0, 1.0], [0.19, 0.78, 0.19, 1.0], [0.54, 0.53, 0.55, 1.0], [0.54, 0.53, 0.55, 1.0], [0.29, 0.29, 0.98, 1.0]]                   # D5, Eb5, E5, F5, Gb5, G5
    
    barline_height = 0.02
    barline_colour = [0.075, 0.075, 0.075, 0.8]
    staff_lines.append(gui_game.add_widget(textures.create_sprite_shape(barline_colour, [staff_pos_x, staff_pos_y - note_spacing + 4 * staff_spacing], [staff_width, barline_height])))
    for i in range(num_staff_lines):
        staff_body_white = textures.create_sprite_shape([0.78, 0.78, 0.78, 0.75], [staff_pos_x, staff_pos_y + i * staff_spacing], [staff_width, staff_spacing - barline_height])
        staff_body_black = textures.create_sprite_shape(barline_colour, [staff_pos_x, staff_pos_y - note_spacing + i * staff_spacing], [staff_width, barline_height])
        staff_lines.append(gui_game.add_widget(staff_body_white))
        staff_lines.append(gui_game.add_widget(staff_body_black))
    
    # Note box and highlights are the boxes that light up indicating what note should be played
    note_box = []
    note_highlight = []
    
    # Score box and highlights are the boxes that light up indicating which notes the player is hitting
    score_box = []
    score_highlight = []

    font_test = textures.create_sprite_texture("trophy_gold.tga", (0.0, 0.0), (1.0, 1.0))
    font_test.texture.texture_id = font_game_h1.texture_id
    gui_game.add_widget(font_test)

    num_notes = 20
    tone_count = 0
    incidental_count = 0
    note_positions = []
    note_start_x = staff_pos_x - (staff_width * 0.5) - 0.1
    note_start_y = staff_pos_y - note_spacing * 3
    score_start_x = note_start_x + 0.2
    for i in range(num_notes):
        note_height = note_spacing
        is_incidental = i in incidentals
        if is_incidental:
            note_height = note_height * 0.5
            
        note_highlight.append(note_base_alpha)
        score_highlight.append(score_base_alpha)
        note_offset = note_start_y + tone_count * note_spacing
        note_size = [note_spacing, note_height]
        score_size = [0.06, note_spacing * 0.84]

        if is_incidental:
            note_box.append(gui_game.add_widget(textures.create_sprite_shape(note_colours[i], [note_start_x - note_spacing - 0.005, note_offset - note_spacing * 0.5], note_size)))
        else:
            note_box.append(gui_game.add_widget(textures.create_sprite_shape(note_colours[i], [note_start_x, note_offset], note_size)))
            
        score_box.append(gui_game.add_widget(textures.create_sprite_shape(note_colours[i], [score_start_x, note_offset], score_size)))
        
        note_positions.append(0.01 * tone_count)
        
        if is_incidental:
            incidental_count += 1
        else:
            tone_count += 1

    # Connect midi inputs and outputs
    devices = MidiDevices()
    devices.open_input_default()
    devices.open_output_default()

    # Read a midi file and load the notes
    music = Music(graphics, textures, [staff_pos_x, staff_pos_y], note_positions, incidentals, os.path.join("music", "test.mid"))

    glViewport(0, 0, window_width, window_height)
    glClearColor(0.0, 0.0, 0.0, 1.0)    
    glShadeModel(GL_SMOOTH) 
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glfw.swap_interval(1)

    score = 0
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

        music_notes = music.draw(music_time)

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
        for i in range(num_notes):
            note_box[i].sprite.set_alpha(note_highlight[i])
            score_box[i].sprite.set_alpha(score_highlight[i])
            if note_highlight[i] > note_base_alpha:
                note_highlight[i] -= 0.9 * dt
            if score_highlight[i] > score_base_alpha:
                score_highlight[i] -= 0.8 * dt

        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        gui_game.draw(dt)

        # Show the score
        font_game_h1.draw(f"{score} XP", [bg_score.sprite.pos[0] + 0.2, bg_score.sprite.pos[1] + 0.05], [0.1, 0.1, 0.1, 1.0])

        # Show a large treble clef to be animated
        font_game_music_large.draw("G", [staff_pos_x - 0.01, staff_pos_y - 0.01], [0,0,0,1.0])

        glfw.swap_buffers(window)

    devices.quit()
    pygame.quit()
    glfw.terminate()
main()
