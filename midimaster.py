import pygame
from texture import TextureManager

def main():
    """The entry point and controlling loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    pygame.init()

    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("MidiMaster")

    subsystems = "gui", "mesh"
    textures = TextureManager("tex", subsystems)
    texLogo = textures.Get("logo.png")
    pygame.display.set_icon(texLogo)
    running = True

    texSplash = textures.GetSub("gui", "imgtitle.tga")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            screen.blit(texSplash, (50, 50))
            pygame.display.flip()

main()
