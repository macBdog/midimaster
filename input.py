import glfw
from enum import Enum
from cursor import Cursor
from mido import Message

action_keyup = 0
action_keydown = 1
action_keyrepeat = 2

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

    def add_key_mapping(self, key: int, val: int):
            self.key_mapping.update({
                key: val
            })

    def handle_cursor_update(self, window, xpos, ypos):
        window_size = glfw.get_framebuffer_size(window)
        self.cursor.pos = [((xpos / window_size[0]) * 2.0) -1.0, ((ypos / window_size[1]) * -2.0) +1.0]

    def handle_mouse_button(self, window, button: int, action: int, mods: int):
        if self.dev_mode:
            print(f"Mouse event log button[{button}], action[{action}], mods[{mods}]")

        # Update the state of each button
        if action == action_keydown:
            self.cursor.buttons[button] = True
        elif action == action_keyup:
            self.cursor.buttons[button] = False

    def handle_input_key(self, window, key: int, scancode: int, action: int, mods: int):
        if self.dev_mode:
            print(f"Input event log key[{key}], scancode[{scancode}], action[{action}], mods[{mods}]")

        # Update the state of each key
        if action == action_keydown:
            self.keys_down[key] = True
        elif action == action_keyup:
            self.keys_down[key] = False

        if key == 256:
            # Esc means quit
            self.running = False
        elif key >= 67 and key <= 73:
            # Check the keyboard keys between A and G for notes - TODO handle incidentals
            key_note_value = key - 67
            if key_note_value < 0:
                key_note_value += 6
            if action == action_keydown:
                new_note = Message('note_on')
                new_note.note = key_note_value + self.staff_pitch_origin
                new_note.velocity = 100
                self.devices.input_messages.append(new_note)
            elif action == action_keyup:
                new_note = Message('note_off')
                new_note.note = key_note_value + self.staff_pitch_origin
                new_note.velocity = 100
                self.devices.input_messages.append(new_note)
        elif key == 61:
            # + Add more space in a bar
            self.note_width_32nd = max(0.0, self.note_width_32nd + (self.dt * 0.1))
        elif key == 45:
            # - Add less space in a bar
            self.note_width_32nd = max(0.0, self.note_width_32nd - (self.dt * 0.1))
        elif key == 262:
            # -> Manually advance forward in time
            self.music_time += self.dt * 5.0
        elif key == 263:
            # <- Manually advance backwards in time
            self.music_time -= self.dt * 5.0
        elif key == 80: 
            # p for Pause on keyup
            if action == action_keyup:
                self.music_running = not self.music_running