import math
from gui import Gui
from input import InputActionKey
from widget import AlignX
from widget import AlignY
from animation import Animation
from animation import AnimType
from music import Music
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

class MidiMaster(Game):
    """The controlling object and main loop for the game. 
        Should always be small and concise, calling out to other managing
        modules and namespaces where possible."""

    def __init__(self):
        super(MidiMaster, self). __init__()
        self.name = "MidiMaster"
        self.music_running = False
        self.note_width_32nd = 0.03
        self.score_highlight = []
        self.note_highlight = []
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.5]
        self.notes_down = {}
        self.num_notes = 20
        self.midi_notes = {}
        self.score = 0
        self.tempo_bpm = 60.0
        self.music_time = 0.0
        self.staff_pitch_origin = 60 # Using middle C4 as the reference note
        self.music_running = False
        self.keyboard_mapping = KeyboardMapping.NOTE_NAMES

    def prepare(self):
        super().prepare()
        self.font_game = Font(os.path.join("ext", "BlackMetalSans.ttf"), self.graphics, self.window)
        music_font = Font(os.path.join("ext", "Musisync.ttf"), self.graphics, self.window)      

        show_intro = False
        if show_intro:
            # Create a background image stretched to the size of the window
            gui_splash = Gui(self.window_width, self.window_height)
            gui_splash.add_widget(self.textures.get("menu_background.tga"), 0, 0)

            # Create a title image and fade it in
            title = gui_splash.add_widget(self.textures.get_sub("gui", "imgtitle.tga"), gui_splash.width / 2, gui_splash.height / 2)
            title.animation = Animation(AnimType.FadeIn, 0.25)

        # Create the holder UI for the game play elements
        self.gui_game = Gui(self.window_width, self.window_height)
        game_bg = self.textures.create_sprite_texture("game_background.tga", (0.0, 0.0), (2.0, 2.0))
        self.gui_game.add_widget(game_bg)

        note_bg_pos_x = 0.228
        note_bg_size = (2.0, 0.333)
        self.note_bg_btm = self.gui_game.add_widget(self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (note_bg_pos_x, -0.24), note_bg_size))
        self.note_bg_top = self.gui_game.add_widget(self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, (note_bg_pos_x, 0.775), (2.0, -0.333)))

        # Draw the 12 note lines with the staff lines of the treble clef highlighted
        staff_pos_x = 0.15
        staff_pos_y = 0.0
        staff_width = 1.85
        staff_lines = []
        note_spacing = 0.085
        staff_spacing = note_spacing * 2
        self.note_base_alpha = 0.15
        self.score_base_alpha = 0.33
        num_staff_lines = 4
        note_colours = [[0.98, 0.25, 0.22, 1.0], [1.0, 0.33, 0.30, 1.0], [0.78, 0.55, 0.99, 1.0], [0.89, 173, 255, 1.0], [1.0, 0.89, 63, 1.0], [0.39, 0.39, 0.55, 1.0], [0.47, 0.47, 0.67, 1.0],  # C4, Db4, D4, Eb4, E4, F4, Gb4
                        [0.89, 0.97, 1.0, 1.0], [0.95, 1.0, 1.0, 1.0], [0.67, 0.1, 0.01, 1.0], [0.78, 0.18, 0.09, 1.0], [0, 0.78, 1.0, 1.0], [1.0, 0.39, 1, 1.0], [1.0, 0.47, 0.1, 1.0],       # G4, Ab4, A4, Bb4, B4, C5, Db5
                        [1.0, 0.375, 0.89, 1.0], [1.0, 0.48, 1.0, 1.0], [0.19, 0.78, 0.19, 1.0], [0.54, 0.53, 0.55, 1.0], [0.54, 0.53, 0.55, 1.0], [0.29, 0.29, 0.98, 1.0]]                   # D5, Eb5, E5, F5, Gb5, G5
        score_colours = note_colours[:]
        
        barline_height = 0.02
        barline_colour = [0.075, 0.075, 0.075, 0.8]
        staff_lines.append(self.gui_game.add_widget(self.textures.create_sprite_shape(barline_colour, [staff_pos_x, staff_pos_y - note_spacing + 4 * staff_spacing], [staff_width, barline_height])))
        for i in range(num_staff_lines):
            staff_body_white = self.textures.create_sprite_shape([0.78, 0.78, 0.78, 0.75], [staff_pos_x, staff_pos_y + i * staff_spacing], [staff_width, staff_spacing - barline_height])
            staff_body_black = self.textures.create_sprite_shape(barline_colour, [staff_pos_x, staff_pos_y - note_spacing + i * staff_spacing], [staff_width, barline_height])
            staff_lines.append(self.gui_game.add_widget(staff_body_white))
            staff_lines.append(self.gui_game.add_widget(staff_body_black))
        
        # Note box and highlights are the boxes that light up indicating what note should be played
        self.note_box = []
        
        # Score box and highlights are the boxes that light up indicating which notes the player is hitting
        self.score_box = []
        tone_count = 0
        note_positions = []
        note_start_x = staff_pos_x - (staff_width * 0.5) - 0.1
        note_start_y = staff_pos_y - note_spacing * 3
        score_start_x = note_start_x + 0.071
        for i in range(self.num_notes):
            note_height = note_spacing
            black_key = i in Music.SharpsAndFlats
            if black_key:
                note_height = note_height * 0.5
                
            self.note_highlight.append(self.note_base_alpha)
            self.score_highlight.append(self.score_base_alpha)
            note_pos = tone_count * note_spacing
            note_offset = note_start_y + note_pos
            note_size = [note_spacing, note_height]
            score_size = [0.05, note_spacing]

            if black_key:
                self.note_box.append(self.gui_game.add_widget(self.textures.create_sprite_shape(note_colours[i], [note_start_x - note_spacing - 0.005, note_offset - note_spacing * 0.5], note_size)))
            else:
                self.note_box.append(self.gui_game.add_widget(self.textures.create_sprite_shape(note_colours[i], [note_start_x, note_offset], note_size)))
                
            self.score_box.append(self.gui_game.add_widget(self.textures.create_sprite_texture_tinted("score_zone.png", score_colours[i], [score_start_x, note_offset], score_size)))
            
            note_positions.append(note_pos)
            
            if not black_key:
                tone_count += 1

        self.setup_input()

        # Read a midi file and load the notes
        self.music = Music(self.graphics, music_font, [staff_pos_x, staff_pos_y], note_positions, os.path.join("music", "mary.mid"))

        # Connect midi inputs and outputs
        self.devices = MidiDevices()
        self.devices.open_input_default()
        self.devices.open_output_default()

    def update(self, dt):
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
                score_id = note - self.staff_pitch_origin
                if score_id >= 0 and score_id < self.num_notes:
                    self.score_highlight[score_id] = 1.0

        self.devices.input_messages = []

        self.gui_game.touch(self.input.cursor)
        self.gui_game.draw(dt)
        music_notes = self.music.draw(dt, self.music_time, self.note_width_32nd)

        if self.music_running:
            self.music_time += dt * (self.tempo_bpm / 60.0) * 10.0

        # Process all notes that have hit the play head
        music_notes_off = {}
        for k in music_notes:
            # Highlight the note box to show this note should be currently played
            if music_notes[k] >= self.music_time:
                highlight_id = k - self.staff_pitch_origin
                self.note_highlight[highlight_id] = 1.0

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
            new_note_off = Message('note_off')
            new_note_off.note = k
            self.devices.output_messages.append(new_note_off)
            self.midi_notes.pop(k)

        # Score points for any score box that is highlighted while a note is lit up
        scored_this_frame = False
        scored_notes = zip(self.note_highlight, self.score_highlight)
        for n, s in scored_notes:
            if n >= 1.0 and s >= 1.0:
                self.score = self.score + 10 * self.dt
                scored_this_frame = True
        
        if scored_this_frame:
            self.note_correct_colour = [1.0 for index, i in enumerate(self.note_correct_colour) if index <=3]
            
        # Highlight score boxes
        self.note_bg_btm.sprite.set_colour(self.note_correct_colour)
        self.note_bg_top.sprite.set_colour(self.note_correct_colour)

        # Pull the scoring box alpha down to 0
        for i in range(self.num_notes):
            self.note_box[i].sprite.set_alpha(self.note_highlight[i])
            self.score_box[i].sprite.set_alpha(self.score_highlight[i])
            self.note_highlight[i] = max(self.note_base_alpha, self.note_highlight[i] - 0.9 * self.dt)
            self.score_highlight[i] = max(self.score_base_alpha, self.score_highlight[i] - 0.8 * self.dt)
        
        # Same with the note highlight background
        self.note_correct_colour = [max(0.6, i - 1.5 * self.dt) for index, i in enumerate(self.note_correct_colour) if index <=3]

        # Show the score on top of everything
        self.font_game.draw(f"{math.floor(self.score)} XP", 22, [self.bg_score.sprite.pos[0], self.bg_score.sprite.pos[1] - 0.03], [0.1, 0.1, 0.1, 1.0])

        # Show developer stats
        if GameSettings.dev_mode:
            cursor_pos = self.input.cursor.pos
            self.font_game.draw(f"FPS: {math.floor(self.fps)}", 12, [0.65, 0.75], [0.81, 0.81, 0.81, 1.0])
            self.font_game.draw(f"X: {math.floor(cursor_pos[0] * 100) / 100}\nY: {math.floor(cursor_pos[1] * 100) / 100}", 10, cursor_pos, [0.81, 0.81, 0.81, 1.0])

        # Update and flush out the buffers
        self.devices.update()
        self.devices.output_messages = []

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
        btn_play = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnplay.tga", (0.62, -0.63), playback_button_size))
        btn_pause = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnpause.tga", (0.45, -0.63), playback_button_size))
        btn_stop = self.gui_game.add_widget(self.textures.create_sprite_texture("gui/btnstop.tga", (0.28, -0.63), playback_button_size))
        
        btn_play.set_action(play, self)
        btn_pause.set_action(pause, self)
        btn_stop.set_action(stop_rewind, self)
        
        self.bg_score = self.gui_game.add_widget(self.textures.create_sprite_texture("score_bg.tga", (-0.33, -0.75), (0.5, 0.25)))
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
            add_note_key_mapping(67, self.staff_pitch_origin)       # C
            add_note_key_mapping(68, self.staff_pitch_origin + 2)   # D
            add_note_key_mapping(69, self.staff_pitch_origin + 4)   # E
            add_note_key_mapping(70, self.staff_pitch_origin + 5)   # F
            add_note_key_mapping(71, self.staff_pitch_origin + 7)   # G
            add_note_key_mapping(65, self.staff_pitch_origin + 9)   # A
            add_note_key_mapping(66, self.staff_pitch_origin + 11)  # B
        elif self.keyboard_mapping == KeyboardMapping.QWERTY_PIANO:
            add_note_key_mapping(81, self.staff_pitch_origin)       # C            
            add_note_key_mapping(50, self.staff_pitch_origin + 1)   # Db
            add_note_key_mapping(87, self.staff_pitch_origin + 2)   # D
            add_note_key_mapping(51, self.staff_pitch_origin + 3)   # Eb
            add_note_key_mapping(69, self.staff_pitch_origin + 4)   # E
            add_note_key_mapping(82, self.staff_pitch_origin + 5)   # F
            add_note_key_mapping(53, self.staff_pitch_origin + 6)   # Gb
            add_note_key_mapping(84, self.staff_pitch_origin + 7)   # G
            add_note_key_mapping(54, self.staff_pitch_origin + 8)   # Ab
            add_note_key_mapping(89, self.staff_pitch_origin + 9)   # A
            add_note_key_mapping(55, self.staff_pitch_origin + 10)  # Bb
            add_note_key_mapping(85, self.staff_pitch_origin + 11)  # B
            add_note_key_mapping(73, self.staff_pitch_origin + 12)  # C

def main():
    """Entry point that creates the MidiMaster object only."""
    mm = MidiMaster()
    mm.prepare()
    mm.begin()

if __name__ == '__main__':
    main()
