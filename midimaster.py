import math
import sys
from gui import Gui
from input import InputActionKey, InputActionModifier
from key_signature import KeySignature
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType
from music import Music
from staff import Staff
from noteboard import NoteBoard
from note_render import NoteRender
from mido import Message
from midi_devices import MidiDevices
from font import Font
from game import Game
from settings import GameSettings
from enum import Enum
from enum import auto
import os.path


class KeyboardMapping(Enum):
    NOTE_NAMES = (0,)
    QWERTY_PIANO = auto()


class MusicMode(Enum):
    PAUSE_AND_LEARN = (0,)
    PERFORMANCE = auto()


class MidiMaster(Game):
    """The controlling object and main loop for the game.
    Should always be small and concise, calling out to other managing
    modules and namespaces where possible."""

    def __init__(self):
        super(MidiMaster, self).__init__()
        self.name = "MidiMaster"
        self.note_width_32nd = 0.025
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.75]
        self.mode = MusicMode.PAUSE_AND_LEARN
        self.keyboard_mapping = KeyboardMapping.NOTE_NAMES
        self.reset()

    def reset(self):
        self.score = 0
        self.music_time = 0.0  # The number of elapsed 32nd notes as a factor of absolute time
        self.notes_down = {}
        self.midi_notes = {}
        self.scored_notes = {}
        self.music_running = False

    def prepare(self):
        super().prepare()
        self.font_game = Font(os.path.join("ext", "BlackMetalSans.ttf"), self.graphics, self.window)
        music_font = Font(os.path.join("ext", "Musisync.ttf"), self.graphics, self.window)

        # Create a background image stretched to the size of the window
        gui_splash = Gui(self.window_width, self.window_height, "splash_screen")
        gui_splash.set_active(True, True)
        self.gui.add_child(gui_splash)
        gui_splash.add_widget(self.textures.create_sprite_texture("menu_background.tga", (0, 0), (2.0, 2.0)))

        # Create a title image and fade it in
        title = gui_splash.add_widget(self.textures.create_sprite_texture("gui/imgtitle.tga", (0, 0), (0.6, 0.6)))
        title.animation = Animation(AnimType.InOutSmooth, GameSettings.DEV_MODE and 0.15 or 2.0)

        # Create the holder UI for the game play elements
        self.gui_game = Gui(self.window_width, self.window_height, "game_screen")
        self.gui.add_child(self.gui_game)

        # Move to the game when the splash is over
        def transition_to_game():
            gui_splash.set_active(False, False)
            self.gui_game.set_active(True, True)

        title.animation.set_action(-1, transition_to_game)

        game_bg = self.textures.create_sprite_texture("game_background.tga", (0.0, 0.0), (2.0, 2.0))
        self.gui_game.add_widget(game_bg)

        self.staff = Staff()
        self.noteboard = NoteBoard()

        note_bg_pos_x = 0.228
        self.note_bg_top = self.gui_game.add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (note_bg_pos_x, self.staff.pos[1] + 0.775), (2.0, -0.35))
        )
        self.note_bg_btm = self.gui_game.add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (note_bg_pos_x, self.staff.pos[1] - 0.705), (2.0, 1.25))
        )

        self.staff.prepare(self.gui_game, self.textures)
        self.noteboard.prepare(self.textures, self.gui_game, self.staff)

        self.score_fade = 0.0
        self.setup_input()

        ref_c4_pos = [self.staff.pos[0] - (self.staff.width * 0.5), self.noteboard.note_positions[60]]
        self.note_render = NoteRender(self.graphics, self.window_width / self.window_height, ref_c4_pos)

        # Read a midi file and load the notes
        level = "test.mid"
        level_path = os.path.join("music", level)
        if os.path.exists(level_path):
            self.music = Music(self.graphics, self.note_render, music_font, self.staff, self.noteboard.get_note_positions(), level_path, 1)

        # Connect midi inputs and outputs
        self.devices = MidiDevices()
        self.devices.open_input_default()
        self.devices.open_output_default()

    def update(self, dt):
        self.profile.begin("midi")

        def score_vfx(note_id = None):
            self.score_fade = 1.0
            self.note_correct_colour = [1.0 for index, i in enumerate(self.note_correct_colour) if index <= 3]
            if note_id is not None:
                spawn_pos = [-0.71, self.noteboard.note_positions[note_id]]
                self.particles.spawn(2.0, spawn_pos, [0.37, 0.82, 0.4, 1.0])

        # Handle events from MIDI input, echo to output so player can hear
        for message in self.devices.input_messages:
            if message.type == "note_on" or message.type == "note_off":
                self.devices.output_messages.append(message)

        # Process any output messages and transfer them to player notes down
        for message in self.devices.output_messages:
            if message.type == "note_on":
                self.notes_down[message.note] = 1.0

                if self.mode == MusicMode.PAUSE_AND_LEARN:
                    if message.note in self.scored_notes:
                        score_vfx(message.note)
                        time_diff = self.music_time - self.scored_notes[message.note]
                        self.score += max(10 - time_diff, 0)
                        del self.scored_notes[message.note]

            elif message.type == "note_off":
                del self.notes_down[message.note]

        # Light up score box for any held note
        for note, velocity in self.notes_down.items():
            if velocity > 0.0:
                self.noteboard.set_score(note)
        self.profile.end()

        self.devices.input_messages = []

        tempo_recip_60 = 1.0 / 60.0
        game_draw, game_input = self.gui_game.is_active()
        if game_draw:
            self.profile.begin("music")
            music_notes = self.music.draw(dt, self.music_time, self.note_width_32nd)
            self.profile.end()

            music_time_advance = dt * Music.SDQNotesPerBeat * (tempo_recip_60 * self.music.tempo_bpm)
            if self.music_running:
                self.music_time += music_time_advance

            # Play the backing track in sync with the player
            self.music.update(self.dt, self.music_time, self.devices)
            self.profile.end()

            # Process all notes that have hit the play head
            self.profile.begin("note_replay")
            music_notes_off = {}
            for k in music_notes:
                # Highlight the note box to show this note should be currently played
                if music_notes[k] >= self.music_time:
                    self.noteboard.note_on(k)

                # The note value in the dictionary is the time to turn off
                if k in self.midi_notes:
                    if self.music_time >= music_notes[k]:
                        music_notes_off[k] = True
                else:
                    self.midi_notes[k] = music_notes[k]
                    self.scored_notes[k] = self.music_time
                    new_note_on = Message("note_on")
                    new_note_on.note = k
                    new_note_on.velocity = 100
                    self.devices.output_messages.append(new_note_on)

            # Send note off messages for all the notes in the music
            for k in music_notes_off:
                del music_notes[k]
                self.noteboard.note_off(k)
                new_note_off = Message("note_off")
                new_note_off.note = k
                self.devices.output_messages.append(new_note_off)
                self.midi_notes.pop(k)
            self.profile.end()

            self.profile.begin("scoring")
            if self.mode == MusicMode.PERFORMANCE:
                if self.noteboard.is_scoring():
                    score_vfx()
                    self.score = self.score + 10 * self.dt
            elif self.mode == MusicMode.PAUSE_AND_LEARN:
                if len(self.scored_notes) > 0 and self.music_running:
                    self.music_time -= music_time_advance

            # Highlight staff background to show score
            self.note_bg_btm.sprite.set_colour(self.note_correct_colour)
            self.note_bg_top.sprite.set_colour(self.note_correct_colour)
            self.noteboard.draw(dt)
            self.profile.end()

            self.profile.begin("text")
            # Same with the note highlight background
            self.note_correct_colour = [max(0.65, i - 0.5 * self.dt) for index, i in enumerate(self.note_correct_colour) if index <= 3]

            # Show the score on top of everything
            self.score_fade -= dt * 0.5
            self.font_game.draw(f"{math.floor(self.score)} XP", 22, [self.bg_score.sprite.pos[0] - 0.025, self.bg_score.sprite.pos[1] - 0.03], [0.1, 0.1, 0.1, 1.0])
            self.profile.end()

        self.profile.begin("dev_mode")
        # Show developer stats
        if GameSettings.DEV_MODE:
            cursor_pos = self.input.cursor.pos
            self.font_game.draw(f"FPS: {math.floor(self.fps)}", 12, [0.65, 0.75], [0.81, 0.81, 0.81, 1.0])
            self.font_game.draw(f"X: {math.floor(cursor_pos[0] * 100) / 100}\nY: {math.floor(cursor_pos[1] * 100) / 100}", 10, cursor_pos, [0.81, 0.81, 0.81, 1.0])
        self.profile.end()

        self.profile.begin("devices")
        # Update and flush out the buffers
        self.devices.update()
        self.devices.output_messages = []
        self.profile.end()

    def end(self):
        super().end()
        self.devices.quit()

    def setup_input(self):
        def play(self):
            self.music_running = True

        def pause(self):
            self.music_running = False

        def stop_rewind(self):
            self.reset()
            self.music.reset()

        def play_button_colour(self):
            return [0.1, 0.87, 0.11, 1.0] if self.music_running else [0.8, 0.8, 0.8, 1.0]

        def pause_button_colour(self):
            return [0.3, 0.27, 0.81, 1.0] if not self.music_running else [0.8, 0.8, 0.8, 1.0]

        def score_bg_colour(self):
            return [1.0, 1.0, 1.0, max(self.score_fade, 0.65)]

        playback_button_size = (0.15, 0.125)
        controls_height = -0.85
        btn_play = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnplay.tga", (0.62, controls_height), playback_button_size))
        btn_pause = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnpause.tga", (0.45, controls_height), playback_button_size))
        btn_stop = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnstop.tga", (0.28, controls_height), playback_button_size))

        btn_play.set_action(play, self)
        btn_play.set_colour_func(play_button_colour, self)
        btn_pause.set_action(pause, self)
        btn_pause.set_colour_func(pause_button_colour, self)
        btn_stop.set_action(stop_rewind, self)

        self.bg_score = self.gui_game.add_widget(self.textures.create_sprite_texture("score_bg.tga", (-0.33, controls_height - 0.10), (0.5, 0.25)))
        self.bg_score.set_colour_func(score_bg_colour, self)
        self.bg_score.align(AlignX.Centre, AlignY.Bottom)

        def note_width_inc():
            self.note_width_32nd = max(0.0, self.note_width_32nd + (self.dt * 0.1))

        def note_width_dec():
            self.note_width_32nd = max(0.0, self.note_width_32nd - (self.dt * 0.1))

        def music_time_fwd():
            self.music_time += self.dt * 30.0

        def music_time_back():
            self.music_time -= self.dt * 30.0

        def music_pause():
            self.music_running = not self.music_running

        self.input.add_key_mapping(32, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, music_pause)  # space for Pause on keyup
        self.input.add_key_mapping(61, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, note_width_inc)  # + Add more space in a bar
        self.input.add_key_mapping(45, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, note_width_dec)  # - Add less space in a bar
        self.input.add_key_mapping(262, InputActionKey.ACTION_KEYREPEAT, InputActionModifier.NONE, music_time_back)  # -> Manually advance forward in time
        self.input.add_key_mapping(263, InputActionKey.ACTION_KEYREPEAT, InputActionModifier.NONE, music_time_fwd)  # -> Manually advance backwards in time

        def create_key_note(note_val: int, note_on: bool):
            note_name = "note_on"
            if note_on == False:
                note_name = "note_off"
            new_note = Message(note_name)
            new_note.note = note_val
            new_note.velocity = 100
            self.devices.input_messages.append(new_note)

        def create_key_note_on(note_val: int):
            create_key_note(note_val, True)

        def create_key_note_off(note_val: int):
            create_key_note(note_val, False)

        def add_note_key_mapping(key_val, note_val, modifier=InputActionModifier.NONE):
            self.input.add_key_mapping(key_val, InputActionKey.ACTION_KEYDOWN, modifier, create_key_note_on, note_val)
            self.input.add_key_mapping(key_val, InputActionKey.ACTION_KEYUP, modifier, create_key_note_off, note_val)

        # Playing notes with the keyboard note names
        if self.keyboard_mapping == KeyboardMapping.NOTE_NAMES:
            note_keycode = 0
            keymap = [67, 68, 69, 70, 71, 65, 66]  # CDEFGAB
            for i in range(NoteBoard.NumNotes):
                note = NoteBoard.OriginNote + i
                note_lookup = note % 12
                if note_lookup in KeySignature.SharpsAndFlats:
                    add_note_key_mapping(keymap[(note_keycode - 1) % 7], note, InputActionModifier.LSHIFT)  # Shift for sharp (#)
                    add_note_key_mapping(keymap[note_keycode % 7], note, InputActionModifier.LCTRL)  # Ctrl for flat (b)
                else:
                    add_note_key_mapping(keymap[note_keycode % 7], note)
                    note_keycode += 1

        elif self.keyboard_mapping == KeyboardMapping.QWERTY_PIANO:
            add_note_key_mapping(81, NoteBoard.OriginNote)  # C
            add_note_key_mapping(50, NoteBoard.OriginNote + 1)  # Db
            add_note_key_mapping(87, NoteBoard.OriginNote + 2)  # D
            add_note_key_mapping(51, NoteBoard.OriginNote + 3)  # Eb
            add_note_key_mapping(69, NoteBoard.OriginNote + 4)  # E
            add_note_key_mapping(82, NoteBoard.OriginNote + 5)  # F
            add_note_key_mapping(53, NoteBoard.OriginNote + 6)  # Gb
            add_note_key_mapping(84, NoteBoard.OriginNote + 7)  # G
            add_note_key_mapping(54, NoteBoard.OriginNote + 8)  # Ab
            add_note_key_mapping(89, NoteBoard.OriginNote + 9)  # A
            add_note_key_mapping(55, NoteBoard.OriginNote + 10)  # Bb
            add_note_key_mapping(85, NoteBoard.OriginNote + 11)  # B
            add_note_key_mapping(73, NoteBoard.OriginNote + 12)  # C


def main():
    """Entry point that creates the MidiMaster object only."""

    if len(sys.argv) > 1:
        GameSettings.DEV_MODE = sys.argv[1].find("debug") or sys.argv[1].find("dev")

    mm = MidiMaster()
    mm.prepare()
    mm.begin()


if __name__ == "__main__":
    main()
