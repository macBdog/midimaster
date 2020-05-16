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
    bg_game = gui_game.add_widget(textures.get("game_background.tga"), 0, 0)
    bg_game.texture.resize(gui_game.width, gui_game.height)

    bg_score = gui_game.add_widget(textures.get("score_bg.tga"), window_width * 0.5, window_height - 100)
    bg_score.align(AlignX.Centre, AlignY.Bottom)

    # Draw the 12 note lines with the staff lines of the treble clef highlighted
    staff_pos_x = 150
    staff_pos_y = window_height // 2
    staff_lines = []
    note_box = []
    note_highlight = []
    note_spacing = 20
    note_base_alpha = 32
    staff_spacing = note_spacing * 2
    num_staff_lines = 4
    num_notes = 12
    staff_pitch_origin = 60 # Using middle C4 as the reference note
    note_start = staff_pos_y + (note_spacing * 3) + (note_spacing // 2) - 2
    note_colours = [(252, 64, 58), (205, 153, 254), (255, 235, 63), (101, 101, 153),    # C, Db, D, Eb
                    (227, 251, 255), (172, 28, 2), (0, 204, 255), (255, 101, 1),        # E, F, Gb, G
                    (255, 96, 236), (50, 205, 51), (140, 138, 141), (75, 75, 252)]      # Ab, A, Bb, B 
    for i in range(num_staff_lines):
        staff_lines.append(gui_game.add_widget(textures.get("staff.png"), staff_pos_x, staff_pos_y - i * staff_spacing))
        staff_lines[i].texture.resize(window_width - 100, staff_spacing)
        staff_lines[i].texture.set_alpha(150)
    for i in range(num_notes):
        note_highlight.append(note_base_alpha)
        note_box.append(gui_game.add_widget(textures.get("note_box.png"), staff_pos_x - note_spacing, note_start - i * note_spacing))
        note_box[i].texture.tint(note_colours[i])
        note_box[i].texture.set_alpha(note_highlight[i])

    # Connect midi inputs and outputs
    devices = MidiDevices()
    devices.open_input_default()
    devices.open_output_default()

    # Read a midi file and load the notes
    music = Music(devices, textures, sprites, (staff_pos_x, staff_pos_y), os.path.join("music", "mary.mid"))

    # Show the score
    score = 0
    text_score = SpriteString(font_game_h1, "{0} XP".format(score), (bg_score.texture.rect.x + 232, bg_score.texture.rect.y + 38), (28, 28, 28))
    sprites.add(text_score)

    # Show a large treble clef to be animated
    text_treble_clef = SpriteString(font_game_music_large, "G", (staff_pos_x - 128, staff_pos_y - 186), (0,0,0))
    sprites.add(text_treble_clef)

    num_fps_samples = 8
    fps_samples = deque()
    clock = pygame.time.Clock()
    desired_framerate = 60

    while running:
        dt = clock.tick(desired_framerate) * 0.001
        
        if len(fps_samples) < num_fps_samples:
            fps_samples.appendleft(dt)
        else:
            fps_samples.pop()
            fps_samples.appendleft(dt)

        devices.update()

        # Handle all events from MIDI input devices
        for message in devices.input_messages:
            if message.type == 'note_on' or message.type == 'note_off':
                score += 100
                highlight_id = message.note - staff_pitch_origin
                if highlight_id >= 0 and highlight_id < num_notes:
                    note_highlight[highlight_id] = 255
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
                    note_highlight[0] = 255
                    text_score.set_text("{0} XP".format(score))
                    new_note = Message('note_on')
                    new_note.note = 60
                    new_note.velocity = 100
                    devices.output_messages.append(new_note)

        gui_game.draw(dt)
        music.draw(dt)

        for i in range(num_notes):
            if note_highlight[i] > note_base_alpha:
                note_highlight[i] -= 4
                note_box[i].texture.set_alpha(note_highlight[i])

        # Update and draw the cached dirty rect list
        sprites.update()
        rects = sprites.draw(screen)
        pygame.display.update(rects)

        # Print the fps when it dips below our target
        total_fps = sum(fps_samples) / num_fps_samples
        if total_fps > 0:
            fps_avg = 1.0 / total_fps;
            if fps_avg < desired_framerate - 2:
                print("Framerate has dipped below target - {0:3.2f}, timing is compromised.".format(fps_avg))

    devices.quit()
    pygame.quit()
main()
