import pygame
import pygame.freetype
from texture import TextureManager
from gui import Gui
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType
from music import Music
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
    gui_splash = Gui(screen, sprites, window_width, window_height)

    texLogo = textures.get("logo.png")
    pygame.display.set_icon(texLogo.image)
    running = True

    # Create a background image stretched to the size of the window
    #bg_splash = gui_splash.add_widget(textures.get("game_background.tga"), 0, 0)
    #bg_splash.texture.image = pygame.transform.scale(bg_splash.texture.image, (gui_splash.width, gui_splash.height))

    # Create a title image and fade it in
    # title = gui_splash.add_widget(textures.get_sub("gui", "imgtitle.tga"), gui_splash.width // 2, gui_splash.height // 2)
    # title.align(AlignX.Centre, AlignY.Middle)
    # title.animation = Animation(AnimType.FadeIn, 1.7)

    # Create the holder UI for the game play elements
    gui_game = Gui(screen, sprites, window_width, window_height)
    bg_game = gui_game.add_widget(textures.get("game_background.tga"), 0, 0)
    bg_game.texture.resize(gui_game.width, gui_game.height)

    bg_score = gui_game.add_widget(textures.get("score_bg.tga"), gui_splash.width * 0.5, gui_splash.height - 100)
    bg_score.align(AlignX.Centre, AlignY.Bottom)

    # Draw the 5 staff lines of the treble clef
    staff_pos_x = 150
    staff_pos_y = gui_splash.height // 2
    staff_lines = []
    staff_spacing = 40
    num_staff_lines = 4
    staff_colours = [(0, 128, 0), (0, 0, 128), (128, 0, 128), (128, 128, 0)]
    for i in range(num_staff_lines):
        staff_lines.append(gui_game.add_widget(textures.get("staff.png"), staff_pos_x, staff_pos_y - i * staff_spacing))
        staff_lines[i].texture.resize(window_width - 100, staff_spacing)
        staff_lines[i].texture.tint(staff_colours[i])
        staff_lines[i].texture.set_alpha(150)

    # Read a midi file and load the notes
    music = Music(screen, textures, sprites, (staff_pos_x, staff_pos_y), os.path.join("music", "mary.mid"))

    # Show the score
    score = 0
    text_score = SpriteString(font_game_h1, "{0} XP".format(score), (232, 38), (28, 28, 28))
    sprites.add(text_score)

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

        # Handle all events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    score += 1
                    text_score.set_text("{0} XP".format(score))
        
        # gui_splash.draw(dt)
        gui_game.draw(dt)
        music.draw(dt)

        # Update and draw the cached dirty rect list
        sprites.update()
        rects = sprites.draw(screen)

        # Draw the treble clef
        font_game_music_large.render_to(screen, (staff_pos_x - 96, staff_pos_y - 186), "G", (0, 0, 0))

        # draw the fps
        total_fps = sum(fps_samples) / num_fps_samples
        if total_fps > 0:
            fps_avg = 1.0 / total_fps;
            if fps_avg < desired_framerate - 2:
                print("Framerate has dipped below target - {0:3.2f}, timing is compromised.".format(fps_avg))

        pygame.display.update()
main()
