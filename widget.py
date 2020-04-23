class Widget:
    """A collection of functionality around the display of a texture.
        Base class can display and animate alpha, width, height. 
        Child classes are expected to handle input and other functionality."""

    def __init__(self, texture, x, y):
        self.texture = texture
        self.width = texture.get_width()
        self.height = texture.get_height()
        self.x = x
        self.y = y
