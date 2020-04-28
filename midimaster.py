import pygame
from texture import TextureManager
from gui import Gui
from widget import AlignX
from widget import AlignY

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

    title = gui.add_widget(textures.get_sub("gui", "imgtitle.tga"), gui.width // 2, gui.height // 2)
    title.alignX = AlignX.Centre
    title.alignY = AlignY.Middle

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            gui.draw()
            pygame.display.flip()

main()
