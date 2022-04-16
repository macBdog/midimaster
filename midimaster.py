import math
from gui import Gui
from input import InputActionKey
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType
from music import Music
from staff import Staff
from noteboard import NoteBoard
from mido import Message
from midi_devices import MidiDevices
from font import Font
from game import Game
from settings import GameSettings
from enum import Enum
from enum import auto
import os.path

class KeyboardMapping(Enum):
    NOTE_NAMES = 0,
    QWERTY_PIANO = auto()

class MusicMode(Enum):
    PAUSE_AND_LEARN = 0,
    PERFORMANCE = auto()

class MidiMaster(Game):
    """The controlling object and main loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    def __init__(self):
        super(MidiMaster, self). __init__()
        self.name = "MidiMaster"
        self.note_width_32nd = 0.03
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.75]
        self.notes_down = {}
        self.midi_notes = {}
        self.score = 0
        self.music_time = 0.0
        self.music_running = False
        self.mode = MusicMode.PAUSE_AND_LEARN
        self.keyboard_mapping = KeyboardMapping.NOTE_NAMES

    def prepare(self):
        super().prepare()
        self.font_game = Font(os.path.join("ext", "BlackMetalSans.ttf"), self.graphics, self.window)
        music_font = Font(os.path.join("ext", "Musisync.ttf"), self.graphics, self.window)      

        # Create a background image stretched to the size of the window
        gui_splash = Gui(self.window_width, self.window_height, "splash_screen")
        gui_splash.set_active(True, True)
        self.gui.add_child(gui_splash)
        gui_splash.add_widget(self.textures.create_sprite_texture("menu_background.tga", (0,0), (2.0, 2.0)))

        # Create a title image and fade it in
        title = gui_splash.add_widget(self.textures.create_sprite_texture("gui/imgtitle.tga", (0, 0), (0.6, 0.6)))
        title.animation = Animation(AnimType.InOutSmooth, GameSettings.dev_mode and 0.15 or 2.0)

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
        self.note_bg_top = self.gui_game.add_widget(self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (note_bg_pos_x, self.staff.pos[1] + 0.775), (2.0, -0.35)))
        self.note_bg_btm = self.gui_game.add_widget(self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (note_bg_pos_x, self.staff.pos[1] - 0.58), (2.0, 1.0)))

        self.staff.prepare(self.gui_game, self.textures)
        self.noteboard.prepare(self.textures, self.gui_game, self.staff)

        self.setup_input()

        # Read a midi file and load the notes
        self.music = Music(self.graphics, music_font, self.staff, self.noteboard.get_note_positions(), os.path.join("music", "test.mid"), 1)

        # Connect midi inputs and outputs
        self.devices = MidiDevices()
        self.devices.open_input_default()
        self.devices.open_output_default()

    def update(self, dt):
        self.profile.begin('midi')

        # Handle events from MIDI input, echo to output so player can hear
        for message in self.devices.input_messages:
            if message.type == 'note_on' or message.type == 'note_off':
                self.devices.output_messages.append(message)

        # Process any output messages and transfer them to player notes down
        for message in self.devices.output_messages:
            if message.type == 'note_on':
                self.notes_down[message.note] = 1.0
            elif message.type == 'note_off':
                self.notes_down[message.note] = 0.0
            
        # Light up score box for any held note
        for note, velocity in self.notes_down.items():
            if velocity > 0.0:
                self.noteboard.set_score(note) 
        self.profile.end()

        self.devices.input_messages = []

        game_draw, game_input = self.gui_game.is_active()
        if game_draw:
            self.profile.begin('music')
            music_notes = self.music.draw(dt, self.music_time, self.note_width_32nd)
            self.profile.end()

            music_time_advance = dt * (self.music.tempo_bpm / 8.0)
            if self.music_running:
                self.music_time += music_time_advance
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
                    if music_notes[k] < self.music_time:
                        music_notes_off[k] = True
                elif music_notes[k] >= self.music_time:   
                    self.midi_notes[k] = music_notes[k]
                    new_note_on = Message('note_on')
                    new_note_on.note = k
                    new_note_on.velocity = 100
                    self.devices.output_messages.append(new_note_on)

            # Send note off messages for all the notes in the music
            for k in music_notes_off:
                self.noteboard.note_off(k)
                new_note_off = Message('note_off')
                new_note_off.note = k
                self.devices.output_messages.append(new_note_off)
                self.midi_notes.pop(k)
            self.profile.end()

            self.profile.begin("scoring")
            
            scored_notes = self.noteboard.get_scored_notes()
            num_scored_notes = len(scored_notes)

            if self.mode == MusicMode.PERFORMANCE:
                if num_scored_notes > 0:
                    self.note_correct_colour = [1.0 for index, i in enumerate(self.note_correct_colour) if index <=3]
                    self.score = self.score + 10 * self.dt
            elif self.mode == MusicMode.PAUSE_AND_LEARN:
                playing_notes = self.noteboard.get_playing_notes()
                num_playing_notes = len(playing_notes)
                if self.music_running:
                    if num_playing_notes > num_scored_notes:
                        self.music_time -= music_time_advance

            # Highlight score boxes
            self.note_bg_btm.sprite.set_colour(self.note_correct_colour)
            self.note_bg_top.sprite.set_colour(self.note_correct_colour)
            self.noteboard.draw(dt)
            self.profile.end()
            
            self.profile.begin("gui")
            # Same with the note highlight background
            self.note_correct_colour = [max(0.65, i - 1.5 * self.dt) for index, i in enumerate(self.note_correct_colour) if index <= 3]

            # Show the score on top of everything
            self.font_game.draw(f"{math.floor(self.score)} XP", 22, [self.bg_score.sprite.pos[0], self.bg_score.sprite.pos[1] - 0.03], [0.1, 0.1, 0.1, 1.0])
            self.profile.end()

        self.profile.begin("dev_mode")
        # Show developer stats
        if GameSettings.dev_mode:
            cursor_pos = self.input.cursor.pos
            self.font_game.draw(f"FPS: {math.floor(self.fps)}", 12, [0.65, 0.75], [0.81, 0.81, 0.81, 1.0])
            self.font_game.draw(f"music time: {math.floor(self.music_time)}", 14, [0.35, 0.55], [0.81, 0.81, 0.81, 1.0])
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
            self.music_running = False
            self.music_time = 0
            self.music.reset()

        playback_button_size = (0.15, 0.125)
        controls_height = -0.85
        btn_play = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnplay.tga", (0.62, controls_height), playback_button_size))
        btn_pause = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnpause.tga", (0.45, controls_height), playback_button_size))
        btn_stop = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnstop.tga", (0.28, controls_height), playback_button_size))
        
        btn_play.set_action(play, self)
        btn_pause.set_action(pause, self)
        btn_stop.set_action(stop_rewind, self)
        
        self.bg_score = self.gui_game.add_widget(self.textures.create_sprite_texture("score_bg.tga", (-0.33, controls_height - 0.10), (0.5, 0.25)))
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

        self.input.add_key_mapping(32, InputActionKey.ACTION_KEYDOWN, music_pause)          # space for Pause on keyup
        self.input.add_key_mapping(61, InputActionKey.ACTION_KEYDOWN, note_width_inc)       # + Add more space in a bar
        self.input.add_key_mapping(45, InputActionKey.ACTION_KEYDOWN, note_width_dec)       # - Add less space in a bar
        self.input.add_key_mapping(262, InputActionKey.ACTION_KEYREPEAT, music_time_back)   # -> Manually advance forward in time
        self.input.add_key_mapping(263, InputActionKey.ACTION_KEYREPEAT, music_time_fwd)    # -> Manually advance backwards in time

        def create_key_note(note_val:int, note_on:bool):
            note_name = 'note_on'
            if note_on == False:
                note_name = 'note_off'
            new_note = Message(note_name)
            new_note.note = note_val
            new_note.velocity = 100
            self.devices.input_messages.append(new_note)

        def create_key_note_on(note_val:int):
            create_key_note(note_val, True)

        def create_key_note_off(note_val:int):
            create_key_note(note_val, False)

        def add_note_key_mapping(key_val, note_val):
            self.input.add_key_mapping(key_val, InputActionKey.ACTION_KEYDOWN, create_key_note_on, note_val)          
            self.input.add_key_mapping(key_val, InputActionKey.ACTION_KEYUP, create_key_note_off, note_val)

        # Playing notes with the keyboard note names. TODO: Shift for one accidental (#) up, Ctrl for flat (b)!
        if self.keyboard_mapping == KeyboardMapping.NOTE_NAMES: 
            add_note_key_mapping(67, NoteBoard.OriginNote)       # C
            add_note_key_mapping(68, NoteBoard.OriginNote + 2)   # D
            add_note_key_mapping(69, NoteBoard.OriginNote + 4)   # E
            add_note_key_mapping(70, NoteBoard.OriginNote + 5)   # F
            add_note_key_mapping(71, NoteBoard.OriginNote + 7)   # G
            add_note_key_mapping(65, NoteBoard.OriginNote + 9)   # A
            add_note_key_mapping(66, NoteBoard.OriginNote + 11)  # B
        elif self.keyboard_mapping == KeyboardMapping.QWERTY_PIANO:
            add_note_key_mapping(81, NoteBoard.OriginNote)       # C            
            add_note_key_mapping(50, NoteBoard.OriginNote + 1)   # Db
            add_note_key_mapping(87, NoteBoard.OriginNote + 2)   # D
            add_note_key_mapping(51, NoteBoard.OriginNote + 3)   # Eb
            add_note_key_mapping(69, NoteBoard.OriginNote + 4)   # E
            add_note_key_mapping(82, NoteBoard.OriginNote + 5)   # F
            add_note_key_mapping(53, NoteBoard.OriginNote + 6)   # Gb
            add_note_key_mapping(84, NoteBoard.OriginNote + 7)   # G
            add_note_key_mapping(54, NoteBoard.OriginNote + 8)   # Ab
            add_note_key_mapping(89, NoteBoard.OriginNote + 9)   # A
            add_note_key_mapping(55, NoteBoard.OriginNote + 10)  # Bb
            add_note_key_mapping(85, NoteBoard.OriginNote + 11)  # B
            add_note_key_mapping(73, NoteBoard.OriginNote + 12)  # C

def main():
    """Entry point that creates the MidiMaster object only."""
    mm = MidiMaster()
    mm.prepare()
    mm.begin()

if __name__ == '__main__':
    main()
