from widget import Widget
from texture import SpriteTexture

class Gui:
    """Manager style functionality for a collection of widget classes. 
        Also convenience functions for window handling."""
    def __init__(self, window_width: int, window_height: int):
        self.width = window_width
        self.height = window_height
        self.widgets = []

    def add_widget(self, sprite: SpriteTexture) -> Widget:
        """Add to the list of widgets to draw for this gui collection
        :param texture: The pygame surface to blit when the widget is drawn
        """
        widget = Widget(sprite)
        self.widgets.append(widget)
        return widget

    def draw(self, dt: float):
        for i in self.widgets:
            i.draw(dt)