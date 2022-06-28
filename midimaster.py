import math
import sys
from gui import Gui
from input import InputActionKey, InputActionModifier
from key_signature import KeySignature
from scrolling_background import ScrollingBackground
from song import Song
from song_book import SongBook
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType
from music import Music
from staff import Staff
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

    @staticmethod
    def get_cmd_argument(values: dict) -> bool:
        """Search the command line args and modify the supplied dictionary with values."""
        found_arg = False
        num_args = len(sys.argv)
        for search in values:
            for i, arg in enumerate(sys.argv):
                if arg.find(search) >= 0:
                    found_arg = True
                    arg_parts = arg.split()
                    if len(arg_parts) > 1:
                        values[search] = arg_parts[1]
                    elif i + 1 < num_args - 1:
                        values[search] = sys.argv[i+1]
        return found_arg

    def __init__(self):
        super(MidiMaster, self).__init__()
        self.name = "MidiMaster"
        self.note_width_32nd = Staff.NoteWidth32nd
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.75]
        self.note_bg_colour = [0.5] * 4
        self.mode = MusicMode.PAUSE_AND_LEARN
        self.keyboard_mapping = KeyboardMapping.NOTE_NAMES
        self.reset()

    def reset(self):
        self.score = 0
        self.music_time = 0.0  # The number of elapsed 32nd notes as a factor of absolute time
        self.player_notes_down = {}
        self.midi_notes = {}
        self.scored_notes = {}
        self.music_running = False

    def prepare(self):
        super().prepare()
        self.font_game = Font(os.path.join("ext", "BlackMetalSans.ttf"), self.graphics, self.window)

        # Create a background image stretched to the size of the window
        gui_splash = Gui(self.window_width, self.window_height, "splash_screen")
        gui_splash.set_active(True, True)
        self.gui.add_child(gui_splash)
        gui_splash.add_widget(self.textures.create_sprite_texture("splash_background.png", (0, 0), (2.0, 2.0)))

        # Create a title image and fade it in
        title = gui_splash.add_widget(self.textures.create_sprite_texture("gui/imgtitle.tga", (0, 0), (0.6, 0.6)))
        title.animation = Animation(AnimType.InOutSmooth, GameSettings.DEV_MODE and 0.15 or 2.0)

        # Create a menu gui
        self.gui_menu = Gui(self.window_width, self.window_height, "menu_screen")
        self.gui_menu.add_widget(self.textures.create_sprite_texture("menu_background.tga", (0, 0), (2.0, 2.0)))
        self.gui.add_child(self.gui_menu)

        # Create the holder UI for the game play elements
        self.gui_game = Gui(self.window_width, self.window_height, "game_screen")
        self.gui.add_child(self.gui_game)

        def transition_to_menu():
            gui_splash.set_active(False, False)
            self.gui_menu.set_active(True, True)

        def transition_to_game():
            gui_splash.set_active(False, False)
            self.gui_game.set_active(True, True)
                
        # Move to the game or menu when the splash is over
        if GameSettings.DEV_MODE:
            title.animation.set_action(-1, transition_to_game)
        else:
            title.animation.set_action(-1, transition_to_menu)
 
        self.gui_game.add_widget(
            self.textures.create_sprite_texture("game_background.tga", (0.0, 0.0), (2.0, 2.0))
        )

        self.bg = ScrollingBackground(self.textures, "menu_glyphs.tga")

        self.staff = Staff()
        
        bg_pos_x = Staff.Pos[0] + Staff.Width * 0.5
        bg_size_top = 0.65
        bg_size_btm = 1.25
        self.note_bg_top = self.gui_game.add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (bg_pos_x, Staff.Pos[1] + (Staff.StaffSpacing * 4.0) + (bg_size_top * 0.5)), (Staff.Width, bg_size_top * -1.0))
        )
        self.note_bg_btm = self.gui_game.add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (bg_pos_x, Staff.Pos[1] - bg_size_btm * 0.5), (Staff.Width, bg_size_btm))
        )
        self.note_bg = self.gui_game.add_widget(
            self.textures.create_sprite_shape(self.note_bg_colour, [Staff.Pos[0] + Staff.Width * 0.5, Staff.Pos[1] + Staff.StaffSpacing * 2.0], (Staff.Width, Staff.StaffSpacing * 4.0))
        )

        self.staff.prepare(self.gui_game, self.textures)
        
        self.score_fade = 0.0
        self.setup_input()

        self.note_render = NoteRender(self.graphics, self.window_width / self.window_height, self.staff)

        # Read the songbook and load the first song
        self.songbook = SongBook.load()
        if self.songbook is None:
            self.songbook = SongBook()

        #Add a new song supplied on the command line
        song_args = {
            "--song-add": "",
            "--song-track": "1",
        }
        if MidiMaster.get_cmd_argument(song_args):
            song_path = os.path.join(".", song_args["--song-add"])
            song_track = int(song_args["--song-track"])
            if os.path.exists(song_path):
                new_song = Song()
                new_song.from_midi_file(song_path, song_track)
                self.songbook.add_song(new_song)
                print(f"Succesfully added {song_path} to data file.")
            else:
                print(f"Cannot find specificed midi file {song_path}! Exiting.")
                exit()

        num_songs = self.songbook.get_num_songs()
        for i in range(num_songs):
            self.gui_menu.add_widget(self.textures.create_sprite_texture("gui/btnplay.tga", (-0.5, 0.8 - i * 0.125), (0.125, 0.1)))

        self.music = Music(self.graphics, self.note_render, self.staff)
        self.music.load(self.songbook.get_default_song())
        
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
                spawn_pos = [-0.71, self.staff.note_positions[note_id]]
                self.particles.spawn(2.0, spawn_pos, [0.37, 0.82, 0.4, 1.0])

        # Handle events from MIDI input, echo to output so player can hear
        for message in self.devices.input_messages:
            if message.type == "note_on" or message.type == "note_off":
                self.devices.output_messages.append(message)

        # Process any output messages and transfer them to player notes down
        for message in self.devices.output_messages:
            if message.type == "note_on":
                self.player_notes_down[message.note] = 1.0

                if self.mode == MusicMode.PAUSE_AND_LEARN:
                    if message.note in self.scored_notes:
                        score_vfx(message.note)
                        time_diff = self.music_time - self.scored_notes[message.note]
                        self.score += max(10 - time_diff, 0)
                        del self.scored_notes[message.note]

            elif message.type == "note_off":
                del self.player_notes_down[message.note]

        # Light up score box for any held note
        for note, velocity in self.player_notes_down.items():
            if velocity > 0.0:
                self.staff.set_score(note)
        self.profile.end()

        self.devices.input_messages = []

        tempo_recip_60 = 1.0 / 60.0
        game_draw, game_input = self.gui_game.is_active()
        if game_draw:
            self.bg.draw(self.dt if self.music_running else self.dt * 0.1)

            self.profile.begin("music")
            music_notes = self.music.draw(dt, self.music_time, self.note_width_32nd)
            self.profile.end()

            music_time_advance = dt * Song.SDQNotesPerBeat * (tempo_recip_60 * self.music.tempo_bpm)
            if self.music_running:
                self.music_time += music_time_advance

            # Play the backing track in sync with the player
            self.music.update(self.dt, self.music_time, self.devices)
            self.profile.end()

            # Process all notes that have hit the play head
            self.profile.begin("note_replay")
            music_notes_off = {}
            for k in music_notes:
                note_off_time = 0
                note_entry = music_notes[k]
                if isinstance(note_entry, list):
                    note_off_time = note_entry[0]
                else:
                    note_off_time = note_entry

                # Highlight the note box to show this note should be currently played
                if note_off_time >= self.music_time:
                    self.staff.note_on(k)

                def new_note_to_play():
                    self.midi_notes[k] = note_off_time
                    self.scored_notes[k] = self.music_time
                    new_note_on = Message("note_on")
                    new_note_on.note = k
                    new_note_on.velocity = 100
                    self.devices.output_messages.append(new_note_on)

                # The note value in the dictionary is the time to turn off
                if k in self.midi_notes:
                    if self.music_time >= note_off_time:
                        music_notes_off[k] = True
                else:
                    new_note_to_play()

            # Send note off messages for all the notes in the music
            for k in music_notes_off:
                del music_notes[k]
                self.staff.note_off(k)
                new_note_off = Message("note_off")
                new_note_off.note = k
                self.devices.output_messages.append(new_note_off)
                self.midi_notes.pop(k)

            self.profile.end()

            self.profile.begin("scoring")
            if self.mode == MusicMode.PERFORMANCE:
                if self.staff.is_scoring():
                    if self.score_fade < 0.5:
                        for note in self.scored_notes:
                            score_vfx(note)
                            break
                    self.score += 10 ** self.dt
            elif self.mode == MusicMode.PAUSE_AND_LEARN:
                if len(self.scored_notes) > 0 and self.music_running:
                    self.music_time -= music_time_advance

            # Highlight staff background to show score
            self.note_bg_btm.sprite.set_colour(self.note_correct_colour)
            self.note_bg_top.sprite.set_colour(self.note_correct_colour)
            self.staff.draw(dt)
            self.profile.end()

            self.profile.begin("text")
            # Same with the note highlight background
            self.note_correct_colour = [max(0.65, i - 0.5 * self.dt) for index, i in enumerate(self.note_correct_colour) if index <= 3]

            # Show the play mode
            mode_string = "Performance" if self.mode == MusicMode.PERFORMANCE else "Pause & Learn"
            self.font_game.draw(f"{mode_string}", 16, [0.5, 0.8], [0.6, 0.6, 0.6, 1.0])

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
        self.songbook.input_device = self.devices.input_device_name
        self.songbook.output_device = self.devices.output_device_name
        SongBook.save(self.songbook)
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

        def mode_toggle(self):
            self.mode = MusicMode.PAUSE_AND_LEARN if self.mode == MusicMode.PERFORMANCE else MusicMode.PERFORMANCE

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
        btn_mode = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/panel_long.png", (0.655, 0.825), (0.32, 0.15)))

        btn_play.set_action(play, self)
        btn_play.set_colour_func(play_button_colour, self)
        btn_pause.set_action(pause, self)
        btn_pause.set_colour_func(pause_button_colour, self)
        btn_stop.set_action(stop_rewind, self)
        btn_mode.set_action(mode_toggle, self)

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
            for i in range(Staff.NumNotes):
                note = Staff.OriginNote + i
                note_lookup = note % 12
                if note_lookup in KeySignature.SharpsAndFlats:
                    add_note_key_mapping(keymap[(note_keycode - 1) % 7], note, InputActionModifier.LSHIFT)  # Shift for sharp (#)
                    add_note_key_mapping(keymap[note_keycode % 7], note, InputActionModifier.LCTRL)  # Ctrl for flat (b)
                else:
                    add_note_key_mapping(keymap[note_keycode % 7], note)
                    note_keycode += 1

        elif self.keyboard_mapping == KeyboardMapping.QWERTY_PIANO:
            add_note_key_mapping(47, Staff.OriginNote)  # C
            add_note_key_mapping(50, Staff.OriginNote + 1)  # Db
            add_note_key_mapping(87, Staff.OriginNote + 2)  # D
            add_note_key_mapping(51, Staff.OriginNote + 3)  # Eb
            add_note_key_mapping(69, Staff.OriginNote + 4)  # E
            add_note_key_mapping(82, Staff.OriginNote + 5)  # F
            add_note_key_mapping(53, Staff.OriginNote + 6)  # Gb
            add_note_key_mapping(84, Staff.OriginNote + 7)  # G
            add_note_key_mapping(54, Staff.OriginNote + 8)  # Ab
            add_note_key_mapping(89, Staff.OriginNote + 9)  # A
            add_note_key_mapping(55, Staff.OriginNote + 10)  # Bb
            add_note_key_mapping(85, Staff.OriginNote + 11)  # B

def main():
    """Entry point that creates the MidiMaster object only."""

    if len(sys.argv) > 1:
        dev_mode_args = {
            "--debug": "",
            "--dev": ""
        }
        GameSettings.DEV_MODE = MidiMaster.get_cmd_argument(dev_mode_args)

    mm = MidiMaster()
    mm.prepare()
    mm.begin()


if __name__ == "__main__":
    main()
