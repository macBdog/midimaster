import pygame
import pygame.freetype
from texture import TextureManager
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
import time
import os.path

def main():
    """The entry point and controlling loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    window_width = 1280
    window_height = 720
    pygame.init()
    font_game_path = os.path.join("ext", "BlackMetalSans.ttf")
    font_music_path = os.path.join("ext", "Musisync.ttf")
    font_game_h1 = pygame.freetype.Font(font_game_path, 50)
    font_game_h2 = pygame.freetype.Font(font_game_path, 38)
    font_game_body = pygame.freetype.Font(font_game_path, 22)
    font_game_music_large = pygame.freetype.Font(font_music_path, 250)

    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("MidiMaster")
    sprites = pygame.sprite.LayeredDirty()

    subsystems = "gui", "mesh"
    textures = TextureManager("tex", subsystems)

    texLogo = textures.get("logo.png")
    pygame.display.set_icon(texLogo.image)
    running = True

    # Create a background image stretched to the size of the window
    # gui_splash = Gui(screen, sprites, window_width, window_height)
    # bg_splash = gui_splash.add_widget(textures.get("game_background.tga"), 0, 0)
    # bg_splash.texture.image = pygame.transform.scale(bg_splash.texture.image, (gui_splash.width, gui_splash.height))

    # Create a title image and fade it in
    # title = gui_splash.add_widget(textures.get_sub("gui", "imgtitle.tga"), gui_splash.width // 2, gui_splash.height // 2)
    # title.align(AlignX.Centre, AlignY.Middle)
    # title.animation = Animation(AnimType.FadeIn, 1.7)

    # Create the holder UI for the game play elements
    gui_game = Gui(sprites, window_width, window_height)
    game_bg = SpriteShape((window_width, window_height), (16, 16, 16))
    gui_game.add_widget(game_bg, 0, 0)

    bg_score = gui_game.add_widget(textures.get("score_bg.tga"), window_width * 0.5, window_height - 100)
    bg_score.align(AlignX.Centre, AlignY.Bottom)

    # Draw the 12 note lines with the staff lines of the treble clef highlighted
    staff_pos_x = 150
    staff_pos_y = window_height // 2
    staff_lines = []
    note_box = []
    note_highlight = []
    note_spacing = 20
    note_base_alpha = 0.15
    staff_spacing = note_spacing * 2
    num_staff_lines = 4
    num_notes = 20
    staff_pitch_origin = 60 # Using middle C4 as the reference note
    note_start = staff_pos_y + (note_spacing * 3) + (note_spacing // 2) + 2
    incidentals = {1: True, 3: True, 6: True, 8: True, 10: True, 13: True, 15: True, 18: True, 20: True}
    note_positions = []
    note_colours = [(252, 64, 58), (255, 84, 78), (205, 153, 254), (225, 173, 255), (255, 235, 63), (101, 101, 153), (121, 121, 173),  # C4, Db4, D4, Eb4, E4, F4, Gb4
                    (227, 251, 255), (247, 255, 255), (172, 28, 2), (192, 48, 22), (0, 204, 255), (255, 101, 1), (255, 121, 21),       # G4, Ab4, A4, Bb4, B4, C5, Db5
                    (255, 96, 236), (255, 116, 255), (50, 205, 51), (140, 138, 141), (140, 138, 141), (75, 75, 252)]                   # D5, Eb5, E5, F5, Gb5, G5
    
    for i in range(num_staff_lines):
        staff_body_white = SpriteShape((window_width - 100, staff_spacing), (200, 200, 200))
        staff_body_black = SpriteShape((window_width - 100, 4), (0, 0, 0))
        staff_lines.append(gui_game.add_widget(staff_body_white, staff_pos_x, staff_pos_y - i * staff_spacing))
        staff_lines.append(gui_game.add_widget(staff_body_black, staff_pos_x, staff_pos_y - i * staff_spacing))
    
    tone_count = 0
    incidental_count = 0
    for i in range(num_notes):
        note_height = note_spacing
        is_incidental = i in incidentals
        if is_incidental:
            note_height = 8
            
        note_highlight.append(note_base_alpha)
        note = SpriteShape((note_spacing, note_height), note_colours[i])
        note.set_alpha(note_highlight[i] * 255)
        if is_incidental:
            note_box.append(gui_game.add_widget(note, staff_pos_x - note_spacing - 12, note_start + 16 - (20 * tone_count)))
        else:
            note_box.append(gui_game.add_widget(note, staff_pos_x - note_spacing, note_start - (20 * tone_count)))

        note_positions.append(20 * tone_count)

        if is_incidental:
            incidental_count += 1
        else:
            tone_count += 1

        
    # Connect midi inputs and outputs
    devices = MidiDevices()
    devices.open_input_default()
    devices.open_output_default()

    # Read a midi file and load the notes
    music = Music(devices, textures, sprites, (staff_pos_x, staff_pos_y), note_positions, incidentals, os.path.join("music", "test.mid"))

    # Show the score
    score = 0
    text_score = SpriteString(font_game_h1, "{0} XP".format(score), (bg_score.texture.rect.x + 232, bg_score.texture.rect.y + 38), (28, 28, 28))
    sprites.add(text_score)

    # Show a large treble clef to be animated
    text_treble_clef = SpriteString(font_game_music_large, "G", (staff_pos_x - 128, staff_pos_y - 186), (0,0,0))
    sprites.add(text_treble_clef)

    music_time = 0.0
    music_running = True
    dt_cur = time.time()
    dt_last = time.time()
    midi_notes = {}
    while running:
        dt_cur = time.time()
        dt = dt_cur - dt_last
        dt_last = dt_cur
        
        devices.update()

        # Handle all events from MIDI input devices
        for message in devices.input_messages:
            if message.type == 'note_on' or message.type == 'note_off':
                score += 100
                highlight_id = message.note - staff_pitch_origin
                if highlight_id >= 0 and highlight_id < num_notes:
                    note_highlight[highlight_id] = 1.0
                devices.output_messages.append(message)

        devices.input_messages = []

        # Handle all events from pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    score += 1
                    note_highlight[0] = 1.0
                    text_score.set_text("{0} XP".format(score))
                    new_note = Message('note_on')
                    new_note.note = 60
                    new_note.velocity = 100
                    devices.output_messages.append(new_note)
                elif event.key == pygame.K_p:
                    music_running = not music_running

        gui_game.draw(dt)
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
            note_box[i].texture.set_alpha(note_highlight[i] * 255)
            if note_highlight[i] > note_base_alpha:
                note_highlight[i] -= 2.0 * dt

        # Update and draw the cached dirty rect list
        sprites.update()
        rects = sprites.draw(screen)
        pygame.display.update(rects)

    devices.quit()
    pygame.quit()
main()
