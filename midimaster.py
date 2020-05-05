import pygame
from texture import TextureManager
from gui import Gui
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType

def main():
    """The entry point and controlling loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    window_width = 1280
    window_height = 720
    pygame.init()
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("MidiMaster")

    subsystems = "gui", "mesh"
    textures = TextureManager("tex", subsystems)
    gui = Gui(screen, window_width, window_height)

    texLogo = textures.get("logo.png")
    pygame.display.set_icon(texLogo)
    running = True

    # Create a background image stretched to the size of the window
    bg = gui.add_widget(textures.get("game_background.tga"), 0, 0)
    bg.alignX = AlignX.Left
    bg.alignY = AlignY.Top
    bg.texture = pygame.transform.scale(bg.texture, (gui.width, gui.height))

    # Create a title image and fade it in
    title = gui.add_widget(textures.get_sub("gui", "imgtitle.tga"), gui.width // 2, gui.height // 2)
    title.alignX = AlignX.Centre
    title.alignY = AlignY.Middle
    title.animation = Animation(AnimType.FadeIn, 1.7)

    clock = pygame.time.Clock()
    while running:
        dt = clock.tick() * 0.001
        
        # Handle all events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Then draw frame
        screen.fill((0,0,0))
        gui.draw(dt)
        pygame.display.flip()

main()
