import enum
from pygame import Surface
from animation import Animation
from texture import SpriteTexture

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

    def __init__(self, texture: SpriteTexture, x: int, y: int):
        self.texture = texture
        self.texture.rect.x = x
        self.texture.rect.y = y
        self.alignX = AlignX.Left
        self.alignY = AlignY.Top
        self.animation = None

    def animate(self, animation: Animation):
        self.animation = animation

    def align(self, x: AlignX, y: AlignY):
        if x == AlignX.Centre:
            self.texture.rect.x -= self.texture.rect.width // 2
        elif x == AlignX.Right:
            self.texture.rect.x -= self.texture.rect.width
        if y == AlignY.Middle:
            self.texture.rect.y -= self.texture.rect.height // 2
        elif y == AlignY.Bottom:
            self.texture.rect.y -= self.texture.rect.height
        self.texture.dirty = 1

    def draw(self, screen: Surface, dt: float):
        """Apply any changes to the widget rect
        :param screen: The pygame.screen used to write the pixel data
        """

        # Apply any active animation
        if self.animation and self.animation.active:
            self.texture.image.set_alpha(int(self.animation.val * 255.0))
            self.texture.dirty = 1
            self.animation.tick(dt)

