from widget import Widget
from texture import SpriteTexture
from cursor import Cursor


class Gui:
    """Manager style functionality for a collection of widget classes.
    Also convenience functions for window handling."""

    def __init__(self, window_width: int, window_height: int, name: str):
        self.name = name
        self.width = window_width
        self.height = window_height
        self.active_draw = False
        self.active_input = False
        self.widgets = []
        self.parent = None
        self.children = {}

    def is_active(self):
        return self.active_draw, self.active_input

    def set_active(self, do_draw: bool, do_input: bool):
        self.active_draw = do_draw
        self.active_input = do_input

    def add_child(self, child):
        if child.name not in self.children and child.parent == None:
            child.parent = self
            self.children[child.name] = child
        else:
            print(f"Error when adding child gui {child.name} to {self.name}! Gui {child.name} already has a parent and it's name is {child.parent.name}.")

    def add_widget(self, sprite: SpriteTexture) -> Widget:
        """Add to the list of widgets to draw for this gui collection
        :param sprite: The underlying sprite OpenGL object that is updated when the widget is drawn."""

        widget = Widget(sprite)
        self.widgets.append(widget)
        return widget

    def touch(self, mouse: Cursor):
        for _, name in enumerate(self.children):
            self.children[name].touch(mouse)

        if self.active_input:
            for i in self.widgets:
                i.touch(mouse)

    def draw(self, dt: float):
        for _, name in enumerate(self.children):
            self.children[name].draw(dt)

        if self.active_draw:
            for i in self.widgets:
                i.draw(dt)
