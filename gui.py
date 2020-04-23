from widget import Widget

class Gui:
    """Manager style functionality for a collection of widget classes. 
        Also convenience functions for window handling."""
    def __init__(self, screen, window_width, window_height):
        self.screen = screen
        self.width = window_width
        self.height = window_height
        self.widgets = []

    def AddWidget(self, texture, x, y):
        self.widgets.append(Widget(texture, x, y))

    def Draw(self):
        for i in self.widgets:
            self.screen.blit(i.texture, (i.x, i.y))