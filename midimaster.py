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
import os.path

def main():
    """The entry point and controlling loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    window_width = 1280
    window_height = 720
    pygame.init()
    font_game_path = os.path.join("ext", "BlackMetalSans.ttf")
    font_game_h1 = pygame.freetype.Font(font_game_path, 50)
    font_game_h2 = pygame.freetype.Font(font_game_path, 38)
    font_game_body = pygame.freetype.Font(font_game_path, 22)

    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("MidiMaster")

    subsystems = "gui", "mesh"
    textures = TextureManager("tex", subsystems)
    gui_splash = Gui(screen, window_width, window_height)

    texLogo = textures.get("logo.png")
    pygame.display.set_icon(texLogo)
    running = True

    # Create a background image stretched to the size of the window
    bg_splash = gui_splash.add_widget(textures.get("menu_background.tga"), 0, 0)
    bg_splash.alignX = AlignX.Left
    bg_splash.alignY = AlignY.Top
    bg_splash.texture = pygame.transform.scale(bg_splash.texture, (gui_splash.width, gui_splash.height))

    # Create a title image and fade it in
    title = gui_splash.add_widget(textures.get_sub("gui", "imgtitle.tga"), gui_splash.width // 2, gui_splash.height // 2)
    title.alignX = AlignX.Centre
    title.alignY = AlignY.Middle
    title.animation = Animation(AnimType.FadeIn, 1.7)

    # Create the holder UI for the game play elements
    gui_game = Gui(screen, window_width, window_height)
    bg_game = gui_game.add_widget(textures.get("game_background.tga"), 0, 0)
    bg_game.alignX = AlignX.Left
    bg_game.alignY = AlignY.Top
    bg_game.texture = pygame.transform.scale(bg_game.texture, (gui_splash.width, gui_splash.height))

    # Draw the 5 staff lines of the treble clef
    staff_pos_x = 50
    staff_pos_y = gui_splash.height // 2
    staff_lines = []
    staff_spacing = 64
    num_staff_lines = 4
    staff_colours = [(0, 128, 0), (0, 0, 128), (128, 0, 128), (128, 128, 0)]
    for i in range(num_staff_lines):
        staff_lines.append(gui_game.add_widget(textures.get("staff.png"), staff_pos_x, staff_pos_y - i * staff_spacing))
        staff_lines[i].alignX = AlignX.Left
        staff_lines[i].alignY = AlignY.Top
        staff_lines[i].texture = pygame.transform.scale(staff_lines[i].texture, (gui_splash.width, staff_spacing))
        staff_lines[i].texture = textures.tint(staff_lines[i].texture, staff_colours[i])
        staff_lines[i].texture.set_alpha(150)

    # Read a midi file and load the notes
    music = Music(screen, textures, (staff_pos_x, staff_pos_y), os.path.join("music", "test.mid"))

    num_fps_samples = 8
    fps_samples = deque()
    clock = pygame.time.Clock()
    while running:
        dt = clock.tick() * 0.001
        
        if len(fps_samples) < num_fps_samples:
            fps_samples.appendleft(dt)
        else:
            fps_samples.pop()
            fps_samples.appendleft(dt)

        # Handle all events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Then draw frame
        screen.fill((0,0,0))

        # gui_splash.draw(dt)
        gui_game.draw(dt)
        music.draw(dt)

        # draw the fps
        total_fps = sum(fps_samples) / num_fps_samples
        if total_fps > 0:
            fps_string = "FPS: {0:3.2f}".format(1.0 / total_fps);
            font_game_body.render_to(screen, (window_width - 200, 50), fps_string, (128, 128, 128))

        pygame.display.flip()

main()
