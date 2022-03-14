import glfw
from enum import Enum
from cursor import Cursor
from mido import Message

class InputActionKey(Enum):
    ACTION_KEYUP = 0
    ACTION_KEYDOWN = 1
    ACTION_KEYREPEAT = 2

class InputMethod(Enum):
    KEYBOARD = 1
    JOYSTICK = 2
    MIDI = 3

class Input():
    """Utility class to handle different methods of input to the game, handles all events from the window system."""

    def __init__(self, window, method: InputMethod):
        self.method = method
        self.window = window
        self.cursor = Cursor()
        self.keys_down = {}
        self.key_mapping = {}
        self.dev_mode = True

        glfw.set_key_callback(window, self.handle_input_key)
        glfw.set_mouse_button_callback(window, self.handle_mouse_button)
        glfw.set_cursor_pos_callback(window, self.handle_cursor_update)

    def add_key_mapping(self, key: int, action:InputActionKey, func, args=None):
            self.key_mapping.update({
                    (key, action): [func, args]
                })

    def add_joystick_mapping(self, button: int, func, args=None):
        pass

    def add_midi_mapping(self, note: int, func, args=None):
        pass

    def handle_cursor_update(self, window, xpos, ypos):
        window_size = glfw.get_framebuffer_size(window)
        self.cursor.pos = [((xpos / window_size[0]) * 2.0) -1.0, ((ypos / window_size[1]) * -2.0) +1.0]

    def handle_mouse_button(self, window, button: int, action: int, mods: int):
        if self.dev_mode:
            print(f"Mouse event log button[{button}], action[{action}], mods[{mods}]")

        # Update the state of each button
        if action == InputActionKey.ACTION_KEYDOWN.value:
            self.cursor.buttons[button] = True
        elif action == InputActionKey.ACTION_KEYUP.value:
            self.cursor.buttons[button] = False

    def handle_input_key(self, window, key: int, scancode: int, action: int, mods: int):
        if self.dev_mode:
            print(f"Input event log key[{key}], scancode[{scancode}], action[{action}], mods[{mods}]")

        # Update the state of each key
        if action == InputActionKey.ACTION_KEYDOWN.value:
            self.keys_down[key] = True
        elif action == InputActionKey.ACTION_KEYUP.value:
            self.keys_down[key] = False

        for _, map in enumerate(self.key_mapping.items()):
            mapping = map[0]
            map_key = mapping[0]
            map_action = mapping[1]
            map_function = map[1]
            if map_key == key and map_action.value == action:
                func = map_function[0]
                args = map_function[1]
                if args is None:
                    func()
                else:
                    func(args)