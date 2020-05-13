from widget import Widget
from pygame import Surface
from pygame import sprite

class Gui:
    """Manager style functionality for a collection of widget classes. 
        Also convenience functions for window handling."""
    def __init__(self, screen: Surface, sprites: sprite.LayeredDirty, window_width: int, window_height: int):
        self.screen = screen
        self.sprites = sprites
        self.width = window_width
        self.height = window_height
        self.widgets = []

    def add_widget(self, texture: Surface, x: int, y: int) -> Widget:
        """Add to the list of widgets to draw for this gui collection
        :param texture: The pygame surface to blit when the widget is drawn
        :param x: Screen horizontal position to display the widget
        :param y: Screen vertical position display the widget
        """
        widget = Widget(texture, x, y)
        self.widgets.append(widget)
        self.sprites.add(widget.texture)
        return widget

    def draw(self, dt: float):
        for i in self.widgets:
            i.draw(self.screen, dt)