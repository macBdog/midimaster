import sys
import os

from album import Album
from gamejam.coord import Coord2d
from gamejam.font import Font
from gamejam.gamejam import GameJam
from gamejam.settings import GameSettings
from gamejam.input import InputActionKey, InputActionModifier

from key_signature import KeySignature
from menu import Menu, Menus
from score import (
    score_player_note_on, score_update_draw, score_setup_display, score_playable_note_on
)
from album_defaults import setup_songbook_albums
from song import Song
from song_book import SongBook
from music import Music
from staff import Staff
from note_render import NoteRender
from mido import Message
from midi_devices import MidiDevices
from menu_func import (
    Dialogs, KeyboardMapping, MusicMode,
    game_play, game_pause, game_stop_rewind, game_back_to_menu, game_mode_toggle,
    game_pause_button_colour, game_play_button_colour,
    song_over,
)


class MidiMaster(GameJam):
    """The controlling object and main loop for the game.
    Should always be small and concise, calling out to other managing
    modules and namespaces where possible."""

    def __init__(self):
        super(MidiMaster, self).__init__()
        self.name = "MidiMaster"
        self.note_width_32nd = Staff.NoteWidth32nd       
        self.mode = MusicMode.PERFORMANCE
        self.keyboard_mapping = KeyboardMapping.NOTE_NAMES

        self.staff: Staff = None
        self.menu: Menu = None
        self.font_game: Font = None
        self.note_render: NoteRender = None
        self.music: Music = None

        self.reset()


    def reset(self):
        self.score = 0
        self.score_max = 0
        self.score_fade = 0.0
        self.music_time = 0.0  # The number of elapsed 32nd notes as a factor of absolute time
        self.player_notes_down = {}
        self.midi_notes = {}
        self.scored_notes = {}
        self.music_running = False

        if self.music:
            self.score_max = self.music.song.get_max_score()


    def prepare(self):
        super().prepare()

        # Add or update any songs supplied on the command line
        self.songbook = setup_songbook_albums()
        song_args = {
            "--song-add": "",
            "--song-track": "1",
            "--song-album": Album.DefaultName,
        }
        if MidiMaster.get_cmd_argument(song_args):
            song_path = os.path.join(".", song_args["--song-add"])
            song_track = int(song_args["--song-track"])
            song_album = int(song_args["--song-album"])

            if os.path.exists(song_path):
                if os.path.isdir(song_path):
                    for file in os.listdir(song_path):
                        full_path = os.path.join(song_path, file)
                        if os.path.isfile(full_path) and file.find("mid") >= 0:
                            self.songbook.add_update_from_midi(full_path, song_track, song_album)
                elif os.path.isfile(song_path):
                    self.songbook.add_update_from_midi(song_path, song_album)
            else:
                print(f"Cannot find specificed midi file or folder {song_path}! Exiting.")
                exit()

        # Connect midi inputs and outputs
        self.devices = MidiDevices()
        if self.songbook.input_device:
            self.devices.open_input(self.songbook.input_device)
        else:
            self.devices.open_input_default()

        if self.songbook.output_device:
            self.devices.open_output(self.songbook.output_device)
        else:
            self.devices.open_output_default()

        # Setup all the game systems
        self.staff = Staff()
        self.menu = Menu(self.graphics, self.input, self.gui, self.devices, self.window_width, self.window_height, self.textures)
        self.font_game = Font(self.graphics, self.window, os.path.join("ext", "BlackMetalSans.ttf"))
        self.staff.prepare(self.menu.get_menu(Menus.GAME), self.textures)
        self.note_render = NoteRender(self.graphics, self.staff)
        self.music = Music(self.graphics, self.note_render, self.staff)
        self.menu.prepare(self.font_game, self.music, self.songbook)

        if GameSettings.DEV_MODE:
            default_song = self.songbook.get_default_song()
            if default_song is None:
                print("Invalid or missing song data file, unable to continue!")
            else:
                self.music.load(default_song)

        self.setup_input()

        #self.score_max = self.music.song.get_max_score()

    def update(self, dt):
        self.menu.update(dt, self.music_running)
        if self.menu.running == False:
            self.quit()

        _, game_draw_active = self.menu.is_menu_active(Menus.GAME)
        if not game_draw_active:
            return

        if self.score_max == 0 and self.music.song is not None:
            self.score_max = self.music.song.get_max_score()

        # Handle events from MIDI input, echo to output so player can hear
        for message in self.devices.get_input_messages():
            if message.type == "note_on" or message.type == "note_off":
                self.devices.output(message)

        # Process any output messages and transfer them to player notes down
        for message in self.devices.get_output_messages():
            if message.type == "note_on":
                self.player_notes_down[message.note] = 1.0
                score_player_note_on(self, message)

            elif message.type == "note_off":
                if message.note in self.player_notes_down:
                    del self.player_notes_down[message.note]

        # Light up score box for any held note
        for note, velocity in self.player_notes_down.items():
            if velocity > 0.0:
                self.staff.set_score(note)

        self.devices.input_flush()

        tempo_recip_60 = 1.0 / 60.0
        game_draw, _ = self.menu.is_menu_active(Menus.GAME)
        if game_draw:
            music_notes = self.music.draw(dt, self.music_time, self.note_width_32nd)

            music_time_advance = dt * Song.SDQNotesPerBeat * (tempo_recip_60 * self.music.tempo_bpm)
            if self.music_running:
                self.music_time += music_time_advance

            # End playback at the end of the song
            if self.music_time >= self.music.song.notes[-1].time + 16:
                self.music_running = False
                self.menu.show_dialog(menu=self.menu, type=Dialogs.GAME_OVER)

            # Play the backing track in sync with the player
            self.music.update(self.dt, self.music_time, self.devices)

            # Process all notes that have hit the play head
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
                    self.devices.output(new_note_on)
                    score_playable_note_on(self, k)

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
                self.devices.output(new_note_off)
                self.midi_notes.pop(k)

            if self.mode == MusicMode.PAUSE_AND_LEARN:
                if len(self.scored_notes) > 0 and self.music_running:
                    self.music_time -= music_time_advance

            self.staff.draw(dt)

            # Show the play mode
            mode_string = "Performance" if self.mode == MusicMode.PERFORMANCE else "Pause & Learn"
            self.font_game.draw(f"{mode_string}", 16, Coord2d(0.5, 0.8), [0.6, 0.6, 0.6, 1.0])

            # Show music time
            if GameSettings.DEV_MODE:
                self.font_game.draw(f"Music Time: {round(self.music_time, 2)}", 12, Coord2d(0.0, 0.8), [0.6, 0.6, 0.6, 1.0])

            score_update_draw(self, dt)

        # Update and flush out the buffers
        self.devices.update()


    def end(self):
        self.songbook.input_device = self.devices.input_device_name
        self.songbook.output_device = self.devices.output_device_name
        SongBook.save(self.songbook)
        super().end()
        self.devices.end()


    def setup_input(self):
        gui = self.menu.get_menu(Menus.GAME)
        btn_mode = gui.add_create_widget(self.textures.create("gui/panel_long.png", Coord2d(0.655, 0.825), Coord2d(0.32, 0.15)))
        btn_mode.set_action(game_mode_toggle, {"game":self})
        
        playback_button_size = Coord2d(0.15, 0.125)
        controls_pos = Coord2d(0.775, -0.85)
        btn_play = gui.add_create_widget(self.textures.create("gui/btnplay.tga", controls_pos - Coord2d(0.035, 0.0), playback_button_size))
        btn_pause = gui.add_create_widget(self.textures.create("gui/btnpause.tga", controls_pos - Coord2d(0.205, 0.0), playback_button_size))
        btn_stop = gui.add_create_widget(self.textures.create("gui/btnstop.tga", controls_pos - Coord2d(0.375, 0.0), playback_button_size))
        
        btn_play.set_action(game_play, {"game":self})
        btn_play.set_colour_func(game_play_button_colour, {"game":self})
        btn_pause.set_action(game_pause, {"game":self})
        btn_pause.set_colour_func(game_pause_button_colour, {"game":self})
        btn_stop.set_action(game_stop_rewind, {"game":self})
        
        btn_menu = gui.add_create_widget(self.textures.create("gui/btnback.png", Coord2d(-0.85, 0.85), Coord2d(0.075, 0.075 * self.window_ratio)))
        btn_menu.set_action(game_back_to_menu, {"game":self})

        game_over = self.menu.get_dialog(Dialogs.GAME_OVER)
        retry_widget = game_over.get_widget("retry")
        retry_widget.set_action(song_over, {"menu": self.menu, "game": self})
        back_widget = game_over.get_widget("back")
        back_widget.set_action(song_over, {"menu": self.menu, "game": self})

        score_setup_display(self, gui, controls_pos)

        def note_width_inc():
            self.note_width_32nd = max(0.0, self.note_width_32nd + (self.dt * 0.1))

        def note_width_dec():
            self.note_width_32nd = max(0.0, self.note_width_32nd - (self.dt * 0.1))

        def music_time_fwd():
            self.music_time += self.dt * 300.0

        def music_time_back():
            self.music_time -= self.dt * 300.0

        def music_pause():
            self.music_running = not self.music_running

        self.input.add_key_mapping(32, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, music_pause)  # space for Pause on keyup
        self.input.add_key_mapping(61, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, note_width_inc)  # + Add more space in a bar
        self.input.add_key_mapping(45, InputActionKey.ACTION_KEYDOWN, InputActionModifier.NONE, note_width_dec)  # - Add less space in a bar
        self.input.add_key_mapping(262, InputActionKey.ACTION_KEYREPEAT, InputActionModifier.NONE, music_time_fwd)  # -> Manually advance forward in time
        self.input.add_key_mapping(263, InputActionKey.ACTION_KEYREPEAT, InputActionModifier.NONE, music_time_back)  # -> Manually retreat backwards in time

        def create_key_note(note_val: int, note_on: bool):
            if self.menu.is_menu_active(Menus.GAME):
                note_name = "note_on"
                if note_on == False:
                    note_name = "note_off"
                new_note = Message(note_name)
                new_note.note = note_val
                new_note.velocity = 100
                self.devices.input(new_note)

        def create_key_note_on(**kwargs):
            note_val = kwargs["note"]
            create_key_note(note_val, True)

        def create_key_note_off(**kwargs):
            note_val = kwargs["note"]
            create_key_note(note_val, False)

        def add_note_key_mapping(key_val, note_val, modifier=InputActionModifier.NONE):
            self.input.add_key_mapping(key_val, InputActionKey.ACTION_KEYDOWN, modifier, create_key_note_on, {"note": note_val})
            self.input.add_key_mapping(key_val, InputActionKey.ACTION_KEYUP, modifier, create_key_note_off, {"note": note_val})

        # Playing notes with the keyboard note names
        starting_note = 48 #C2
        if self.keyboard_mapping == KeyboardMapping.NOTE_NAMES:
            note_keycode = 0
            keymap = [67, 68, 69, 70, 71, 65, 66]  # CDEFGAB
            for i in range(Staff.NumNotes):
                note = starting_note + i
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


def main():
    """Entry point that creates the MidiMaster object only."""

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
