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
        self.alignX = AlignX.Centre
        self.alignY = AlignY.Middle
        self.animation = None

    def animate(self, animation: Animation):
        self.animation = animation

    def align(self, x: AlignX, y: AlignY):
        if x == AlignX.Left:
            self.sprite.pos = (self.sprite.pos[0] - self.sprite.size[0] * 0.5, self.sprite.pos[1])
        elif x == AlignX.Centre:
            pass;
        elif x == AlignX.Right:
            self.sprite.pos = (self.sprite.pos[0] + self.sprite.size[0] * 0.5, self.sprite.pos[1])
        if y == AlignY.Top:
            self.sprite.pos = (self.sprite.pos[0], self.sprite.pos[1] - self.sprite.size[1] * 0.5)
        elif y == AlignY.Middle:
            pass;
        elif y == AlignY.Bottom:
            self.sprite.pos = (self.sprite.pos[0], self.sprite.pos[1] + self.sprite.size[1] * 0.5)

    def draw(self, dt: float):
        """Apply any changes to the widget rect."""

        # Apply any active animation
        if self.animation and self.animation.active:
            self.sprite.set_alpha(self.animation.val)
            self.animation.tick(dt)

        self.sprite.draw()

