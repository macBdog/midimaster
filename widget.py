import enum
from animation import Animation
from texture import SpriteTexture
from cursor import Cursor

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
        self.touched = False
        self.hover_begin = None
        self.hover_end = None
        self.action = None
        self.action_arg = None
        self.colour_func = None
        self.colour_arg = None
        self.actioned = False
        self.alpha_start = self.sprite.colour[3]
        self.alpha_hover = -0.25

    def hover_begin_default(self):
        self.sprite.set_alpha(self.alpha_start + self.alpha_hover)

    def hover_end_default(self):
        self.sprite.set_alpha(self.alpha_start)

    def set_colour_func(self, colour_func, colour_arg = None):
        """ Set a function that determines the colour of a button."""

        self.colour_func = colour_func
        self.colour_arg = colour_arg

    def set_action(self, activation_func, activation_arg = None):
        """Set the function to call on activate. Leave the hover functions defaulted."""

        self.action = activation_func
        self.action_arg = activation_arg
        self.on_hover_begin = self.hover_begin_default
        self.on_hover_end = self.hover_end_default

    def set_actions(self, activation_func, hover_start_func, hover_end_func, activation_arg):
        """Set the function to call on activate with custom hover start and end functions."""

        self.hover_begin = hover_start_func
        self.hover_end = hover_end_func
        self.action = activation_func
        self.action_arg = activation_arg

    def on_hover_begin(self):
        pass

    def on_hover_end(self):
        pass

    def on_activate(self):
        pass

    def animate(self, animation: Animation):
        self.animation = animation

    def align(self, x: AlignX, y: AlignY):
        if x == AlignX.Left:
            self.sprite.pos = (self.sprite.pos[0] - self.sprite.size[0] * 0.5, self.sprite.pos[1])
        elif x == AlignX.Centre:
            pass
        elif x == AlignX.Right:
            self.sprite.pos = (self.sprite.pos[0] + self.sprite.size[0] * 0.5, self.sprite.pos[1])
        if y == AlignY.Top:
            self.sprite.pos = (self.sprite.pos[0], self.sprite.pos[1] - self.sprite.size[1] * 0.5)
        elif y == AlignY.Middle:
            pass
        elif y == AlignY.Bottom:
            self.sprite.pos = (self.sprite.pos[0], self.sprite.pos[1] + self.sprite.size[1] * 0.5)

    def touch(self, mouse: Cursor):
        """Test for activation and hover states."""
        if self.action is not None:
            size_half = [i * 0.5 for i in self.sprite.size]
            inside = (  mouse.pos[0] >= self.sprite.pos[0] - size_half[0] and
                        mouse.pos[0] <= self.sprite.pos[0] + size_half[0] and
                        mouse.pos[1] >= self.sprite.pos[1] - size_half[1] and
                        mouse.pos[1] <= self.sprite.pos[1] + size_half[1])
            if self.touched:
                if not inside:
                    self.on_hover_end()
                    self.touched = False
            else:
                if inside:
                    self.on_hover_begin()
                    self.touched = True

            # Perform the action on mouse up
            if inside:
                if mouse.buttons[0]:
                    if not self.actioned:
                        self.action(self.action_arg)
                        self.actioned = True
            if not mouse.buttons[0]:
                self.actioned = False

    def draw(self, dt: float):
        """Apply any changes to the widget rect."""

        # Apply any colour changes
        if self.colour_func is not None:
            self.sprite.set_colour(self.colour_func(self.colour_arg))

        # Apply any active animation
        if self.animation and self.animation.active:
            self.sprite.set_alpha(self.animation.val)
            self.animation.tick(dt)

        self.sprite.draw()

