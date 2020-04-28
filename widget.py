import enum
from pygame import Surface

class AlignX(enum.Enum):
    Left = 1
    Centre = 2
    Right = 3

class AlignY(enum.Enum):
    Top = 1
    Middle = 2
    Bottom = 3

class Widget:
    """A collection of functionality around the display of a texture.
        Base class can display and animate alpha, width, height. 
        Child classes are expected to handle input and other functionality."""

    def __init__(self, texture: Surface, x: int, y: int):
        self.texture = texture
        self.width = texture.get_width()
        self.height = texture.get_height()
        self.x = x
        self.y = y
        self.alignX = AlignX.Left
        self.alignY = AlignY.Top

    def draw(self, screen):
        """Blit a widget to the screen
        :param screen: The pygame.screen used to write the pixel data
        """
        dX = self.x
        dY = self.y
        if self.alignX == AlignX.Centre:
            dX -= self.width // 2
        elif self.alignX == AlignX.Right:
            dX -= self.width

        if self.alignY == AlignY.Middle:
            dY -= self.height // 2
        elif self.alignY == AlignY.Bottom:
            dY -= self.height

        screen.blit(self.texture, (dX, dY))
