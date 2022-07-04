import math
import sys
import os

from gamejam.font import Font
from gamejam.gamejam import GameJam
from gamejam.settings import GameSettings
from gamejam.widget import AlignX
from gamejam.widget import AlignY
from gamejam.input import InputActionKey, InputActionModifier

from key_signature import KeySignature
from menu import Menu, Menus
from song import Song
from song_book import SongBook
from music import Music
from staff import Staff
from note_render import NoteRender
from mido import Message
from midi_devices import MidiDevices
from enum import Enum, auto


class KeyboardMapping(Enum):
    NOTE_NAMES = (0,)
    QWERTY_PIANO = auto()


class MusicMode(Enum):
    PAUSE_AND_LEARN = (0,)
    PERFORMANCE = auto()


class MidiMaster(GameJam):
    """The controlling object and main loop for the game.
    Should always be small and concise, calling out to other managing
    modules and namespaces where possible."""

    def __init__(self):
        super(MidiMaster, self).__init__()
        self.name = "MidiMaster"
        self.note_width_32nd = Staff.NoteWidth32nd       
        self.mode = MusicMode.PAUSE_AND_LEARN
        self.keyboard_mapping = KeyboardMapping.NOTE_NAMES
        self.reset()


    def reset(self):
        self.score = 0
        self.score_fade = 0.0
        self.music_time = 0.0  # The number of elapsed 32nd notes as a factor of absolute time
        self.player_notes_down = {}
        self.midi_notes = {}
        self.scored_notes = {}
        self.music_running = False


    def prepare(self):
        super().prepare()
        
        # Read the songbook and load the first song
        self.songbook = SongBook.load()
        if self.songbook is None:
            self.songbook = SongBook()
        self.songbook.validate()
        self.songbook.sort()

        # Add a new song supplied on the command line
        song_args = {
            "--song-add": "",
            "--song-track": "1",
        }
        if MidiMaster.get_cmd_argument(song_args):
            song_path = os.path.join(".", song_args["--song-add"])
            song_track = int(song_args["--song-track"])
            
            def add_song(path:str, track=None):
                new_song = Song()
                new_song.from_midi_file(path, track)
                self.songbook.add_song(new_song)
                print(f"Succesfully added {song_path} to data file.")

            if os.path.exists(song_path):
                if os.path.isdir(song_path):
                    for file in os.listdir(song_path):
                        full_path = os.path.join(song_path, file)
                        if os.path.isfile(full_path) and file.find("mid") >= 0:
                            add_song(full_path, song_track)    
                elif os.path.isfile(song_path):
                    add_song(song_path, song_track)                
            else:
                print(f"Cannot find specificed midi file or folder {song_path}! Exiting.")
                exit()

        # Setup all the game systems
        self.staff = Staff()
        self.menu = Menu(self.graphics, self.gui, self.window_width, self.window_height, self.textures)
        self.font_game = Font(os.path.join("ext", "BlackMetalSans.ttf"), self.graphics, self.window)
        self.staff.prepare(self.menu.get_menu(Menus.GAME), self.textures)
        self.note_render = NoteRender(self.graphics, self.window_width / self.window_height, self.staff)
        self.music = Music(self.graphics, self.note_render, self.staff)
        self.menu.prepare(self.font_game, self.music, self.songbook)
        
        if GameSettings.DEV_MODE:
            default_song = self.songbook.get_default_song()
            if default_song is None:
                print("Invalid or missing song data file, unable to continue!")
            else:
                self.music.load(default_song)
        
        # Connect midi inputs and outputs and player input
        self.devices = MidiDevices()
        self.devices.open_input_default()
        self.devices.open_output_default()
        self.setup_input()

    def update(self, dt):

        self.menu.update(dt, self.music_running)

        def score_vfx(note_id = None):
            self.score_fade = 1.0
            self.menu.set_event("score_vfx")
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

        self.devices.input_messages = []

        tempo_recip_60 = 1.0 / 60.0
        game_draw, _ = self.menu.is_menu_active(Menus.GAME)
        if game_draw:
            music_notes = self.music.draw(dt, self.music_time, self.note_width_32nd)

            music_time_advance = dt * Song.SDQNotesPerBeat * (tempo_recip_60 * self.music.tempo_bpm)
            if self.music_running:
                self.music_time += music_time_advance

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

            self.staff.draw(dt)
 
            # Show the play mode
            mode_string = "Performance" if self.mode == MusicMode.PERFORMANCE else "Pause & Learn"
            self.font_game.draw(f"{mode_string}", 16, [0.5, 0.8], [0.6, 0.6, 0.6, 1.0])

            # Show the score on top of everything
            self.score_fade -= dt * 0.5
            self.font_game.draw(f"{math.floor(self.score)} XP", 22, [self.bg_score.sprite.pos[0] - 0.025, self.bg_score.sprite.pos[1] - 0.03], [0.1, 0.1, 0.1, 1.0])

        # Show developer stats
        if GameSettings.DEV_MODE:
            cursor_pos = self.input.cursor.pos
            self.font_game.draw(f"FPS: {math.floor(self.fps)}", 12, [0.65, 0.75], [0.81, 0.81, 0.81, 1.0])
            self.font_game.draw(f"X: {math.floor(cursor_pos[0] * 100) / 100}\nY: {math.floor(cursor_pos[1] * 100) / 100}", 10, cursor_pos, [0.81, 0.81, 0.81, 1.0])

        # Update and flush out the buffers
        self.devices.update()
        self.devices.output_messages = []


    def end(self):
        self.songbook.input_device = self.devices.input_device_name
        self.songbook.output_device = self.devices.output_device_name
        SongBook.save(self.songbook)
        super().end()
        self.devices.end()


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

        def back_to_menu(self):
            pause(self)
            existing_score = self.music.song.score[self.mode] if self.mode in self.music.song.score else 0
            self.music.song.score[self.mode] = max(self.score, existing_score)
            self.menu.transition(Menus.GAME, Menus.SONGS)

        def play_button_colour(self):
            return [0.1, 0.87, 0.11, 1.0] if self.music_running else [0.8, 0.8, 0.8, 1.0]

        def pause_button_colour(self):
            return [0.3, 0.27, 0.81, 1.0] if not self.music_running else [0.8, 0.8, 0.8, 1.0]

        def score_bg_colour(self):
            return [1.0, 1.0, 1.0, max(self.score_fade, 0.65)]

        playback_button_size = (0.15, 0.125)
        controls_height = -0.85
        gui = self.menu.get_menu(Menus.GAME)
        btn_play = gui.add_widget(self.textures.create_sprite_texture("gui/btnplay.tga", (0.62, controls_height), playback_button_size))
        btn_pause = gui.add_widget(self.textures.create_sprite_texture("gui/btnpause.tga", (0.45, controls_height), playback_button_size))
        btn_stop = gui.add_widget(self.textures.create_sprite_texture("gui/btnstop.tga", (0.28, controls_height), playback_button_size))
        btn_mode = gui.add_widget(self.textures.create_sprite_texture("gui/panel_long.png", (0.655, 0.825), (0.32, 0.15)))
        btn_menu = gui.add_widget(self.textures.create_sprite_texture("gui/btnback.png", (-0.85, 0.85), (0.075, 0.075 * self.window_ratio)))

        btn_play.set_action(play, self)
        btn_play.set_colour_func(play_button_colour, self)
        btn_pause.set_action(pause, self)
        btn_pause.set_colour_func(pause_button_colour, self)
        btn_stop.set_action(stop_rewind, self)
        btn_mode.set_action(mode_toggle, self)
        btn_menu.set_action(back_to_menu, self)

        self.bg_score = gui.add_widget(self.textures.create_sprite_texture("score_bg.tga", (-0.33, controls_height - 0.10), (0.5, 0.25)))
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
            if self.menu.is_menu_active(Menus.GAME):
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
