import enum
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
    """A collection of functionality around the display of a texture for interfaces.
        It owns a reference to a SpriteTexture or SpriteShape for drawing.
        Base class can display and animate alpha, width, height. 
        Child classes are expected to handle input and other functionality."""

    def __init__(self, sprite: SpriteTexture):
        self.sprite = sprite
        self.alignX = AlignX.Left
        self.alignY = AlignY.Top
        self.animation = None

    def animate(self, animation: Animation):
        self.animation = animation

    def align(self, x: AlignX, y: AlignY):
        if x == AlignX.Centre:
            pass
            #self.texture.rect.move_ip(-self.texture.rect.width // 2, 0)
        elif x == AlignX.Right:
            pass
            #self.texture.rect.move_ip(-self.texture.rect.width, 0)
        if y == AlignY.Middle:
            pass
            #self.texture.rect.move_ip(0, -self.texture.rect.height // 2)
        elif y == AlignY.Bottom:
            pass
            #self.texture.rect.move_ip(0, -self.texture.rect.height)

    def draw(self, dt: float):
        """Apply any changes to the widget rect
        :param screen: The pygame.screen used to write the pixel data
        """

        # Apply any active animation
        if self.animation and self.animation.active:
            #self.texture.image.set_alpha(int(self.animation.val * 255.0))
            #self.texture.dirty = 1
            self.animation.tick(dt)

        self.sprite.draw()

