class Cursor:
    """Encapsulates mouse, touch and other constant motion input devices that
    move on a 2D plane with 1 or more boolean inputs."""
    def __init__(self):
        self.pos = [0.0, 0.0]
        self.buttons = {0: False, 2: False, 3: False, 4: False}