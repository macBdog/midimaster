import time
from enum import Enum, auto

from gamejam.animation import Animation, AnimType
from gamejam.gui import Gui
from gamejam.input import Input
from gamejam.settings import GameSettings
from gamejam.quickmaff import lerp, clamp

from song import Song
from staff import Staff
from midi_devices import MidiDevices
from scrolling_background import ScrollingBackground


class Menus(Enum):
    SPLASH = auto()
    SONGS = auto()
    GAME = auto()


class Dialogs(Enum):
    DEVICES = auto()
    GAME_OVER = auto()


class Menu():
    SONG_SPACING = 0.25
    DIALOG_COLOUR = [0.26, 0.15, 0.32, 1.0]

    """Utility class to separate all the gui element drawing from main game logic."""
    def __init__(self, graphics, input: Input, gui: Gui, devices: MidiDevices, width: int, height: int, textures):
        self.menus = {}
        self.dialogs = {}
        self.elements = {m:{} for m in Menus}        
        self.graphics = graphics
        self.input = input
        self.devices = devices
        self.window_width = width
        self.window_height = height
        self.window_ratio = width / height
        self.textures = textures
        self.song_widgets = []
        self.song_scroll = 0.0
        self.song_scroll_target = 0.0
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.75]
        self.running = True

        def quit(self):
            self.running = False

        self.input.cursor.set_sprite(self.textures.create_sprite_texture("gui/cursor.png", [0, 0], [0.25, 0.25 * self.window_ratio]))

        # Create sub-guis for each screen of the game, starting with active splash screen
        self.menus[Menus.SPLASH] = Gui("splash_screen")
        self.menus[Menus.SPLASH].set_active(True, True)
        self.menus[Menus.SPLASH].add_widget(self.textures.create_sprite_texture("splash_background.png", [0, 0], [2.0, 2.0]))
        gui.add_child(self.menus[Menus.SPLASH])

        self.menus[Menus.SONGS] = Gui("menu_screen")
        self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/menu_bg.png", [0, 0], [2.0, 2.0]))
        gui.add_child(self.menus[Menus.SONGS])

        title = self.menus[Menus.SPLASH].add_widget(self.textures.create_sprite_texture("gui/imgtitle.tga", [0, 0], [0.6, 0.6]))
        title.animation = Animation(AnimType.InOutSmooth, 0.15 if GameSettings.DEV_MODE else 2.0)
        self._set_elem(Menus.SPLASH, "title", title)
        
        game_bg_pos_x = Staff.Pos[0] + Staff.Width * 0.5
        self.menus[Menus.GAME] = Gui("game_screen")
        self.menus[Menus.GAME].add_widget(self.textures.create_sprite_texture("game_background.tga", [0, 0], [2.0, 2.0]))
        self.menus[Menus.GAME].add_widget(self.textures.create_sprite_shape([0.5] * 4, [game_bg_pos_x, Staff.Pos[1] + Staff.StaffSpacing * 2.0], [Staff.Width, Staff.StaffSpacing * 4.0]))
        gui.add_child(self.menus[Menus.GAME])

        bg_size_top = 0.65
        bg_size_btm = 1.25
        note_bg_top = self.menus[Menus.GAME].add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, [game_bg_pos_x, Staff.Pos[1] + (Staff.StaffSpacing * 4.0) + (bg_size_top * 0.5)], [Staff.Width, bg_size_top * -1.0])
        )
        note_bg_btm = self.menus[Menus.GAME].add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, [game_bg_pos_x, Staff.Pos[1] - bg_size_btm * 0.5], [Staff.Width, bg_size_btm])
        )
        self._set_elem(Menus.GAME, "note_bg_top", note_bg_top)
        self._set_elem(Menus.GAME, "note_bg_btm", note_bg_btm)
        self._set_elem(Menus.GAME, "bg", ScrollingBackground(self.graphics, self.textures, "menu_glyphs.tga"))

        # Create the dialogs
        dialog_size = [0.8, 1.1]
        self.dialogs[Dialogs.DEVICES] = Gui("devices")
        self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_shape(Menu.DIALOG_COLOUR, [0, 0], dialog_size))
        delete_widget = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/checkboxon.tga", [dialog_size[0] * 0.5, dialog_size[1] * 0.5], [0.05, 0.05 * self.window_ratio]))
        delete_widget.set_action(self.hide_dialog, Dialogs.DEVICES)
        gui.add_child(self.dialogs[Dialogs.DEVICES])

        # Move to the game or menu when the splash is over
        if GameSettings.DEV_MODE:
            title.animation.set_action(-1, self.transition(Menus.SPLASH, Menus.GAME))
        else:
            title.animation.set_action(-1, self.transition(Menus.SPLASH, Menus.SONGS))


    def _get_elem(self, menu: Menus, name: str):
        return self.elements[menu][name]


    def _set_elem(self, menu: Menus, name: str, widget):
        self.elements[menu][name] = widget


    def _set_song_menu_pos(self):
        num_songs = self.songbook.get_num_songs()
        for i in range(num_songs):
            song_pos = [-0.333, (0.4 - i * Menu.SONG_SPACING) + self.song_scroll]
            track_pos = [song_pos[0] + 0.125, song_pos[1] - 0.1]
            widgets_for_song = self.song_widgets[i]
            widgets_for_song["play"].set_pos(song_pos)
            widgets_for_song["delete"].set_pos([song_pos[0]-0.09, song_pos[1]])
            widgets_for_song["reload"].set_pos([song_pos[0]-0.14, song_pos[1]])
            widgets_for_song["score"].set_pos([song_pos[0] + 0.75, song_pos[1]])
            widgets_for_song["track_display"].set_pos([track_pos[0], track_pos[1]])
            widgets_for_song["track_down"].set_pos([track_pos[0]-0.02, track_pos[1] + 0.02])
            widgets_for_song["track_up"].set_pos([track_pos[0]+0.3, track_pos[1] + 0.02])


    def prepare(self, font, music, songbook):
        self.font = font
        self.music = music
        self.songbook = songbook

        def song_play(song_id: int):
            self.music.load(self.songbook.get_song(song_id))
            self.transition(Menus.SONGS, Menus.GAME)

        def song_reload(song_id: int):
            existing_song = self.songbook.get_song(song_id)
            new_song = Song()
            new_song.from_midi_file(existing_song.path, existing_song.player_track_id)
            self.songbook.add_update_song(new_song)
            self._set_song_menu_pos()

        def song_delete(song_id: int):
            widgets = self.song_widgets[song_id]
            for elem in widgets:
                self.menus[Menus.SONGS].delete_widget(widgets[elem])
            self.song_widgets.pop(song_id)
            self.songbook.delete_song(song_id)
            self._set_song_menu_pos()

        def song_track_up(song_id: int):
            song = self.songbook.get_song(song_id)
            song.player_track_id += 1
            song.dirty = True
            widget = self.song_widgets[song_id]
            widget["track_display"].set_text(get_track_display_text(song), 9, None)

        def song_track_down(song_id: int):
            song = self.songbook.get_song(song_id)
            song.player_track_id = max(song.player_track_id-1, 0)
            song.dirty = True
            widget = self.song_widgets[song_id]
            widget["track_display"].set_text(get_track_display_text(song), 9, None)

        def song_list_scroll(dir: float):
            scroll_max = len(self.song_widgets) * Menu.SONG_SPACING
            self.song_scroll_target = clamp(self.song_scroll_target + dir, 0, scroll_max)
            self._set_song_menu_pos()

        def get_track_display_text(song) -> str:
            track = song.player_track_id
            if track in song.track_names:
                return f"{song.player_track_id}: ({song.track_names[song.player_track_id]})"
            else:
                return f"Track {song.player_track_id} (Unknown)"

        # Scroll indicator for song list
        self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_shape([0.1, 0.1, 0.1, 0.5], [0.9, 0.0], [0.05, 1.6]))
        self.scroll_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/sliderknob.png", [0.9, 0.73], [0.035, 0.035 * self.window_ratio]))
        scroll_up_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnup.png", [0.9, 0.8], [0.05, 0.05 * self.window_ratio]))
        scroll_up_widget.set_action(song_list_scroll, -0.333)
        scroll_down_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnup.png", [0.9,-0.8], [0.05, -0.05 * self.window_ratio]))
        scroll_down_widget.set_action(song_list_scroll, 0.333)

        num_songs = self.songbook.get_num_songs()
        for i in range(num_songs):
            song = self.songbook.get_song(i)

            play_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnplay.tga", [0,0], [0.125, 0.1]), self.font)
            play_widget.set_text(song.get_name(), 12, [0.08, -0.02])
            play_widget.set_text_colour([0.85, 0.85, 0.85, 0.85])
            play_widget.set_action(song_play, i)

            score_widget = self.menus[Menus.SONGS].add_widget(None, self.font)

            performance_score = 0
            score_widget.set_text(f"{round((performance_score / song.get_max_score()) * 100.0, 1)}%", 14, [0,0])

            delete_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btntrash.png", [0,0], [0.05, 0.05 * self.window_ratio]))
            delete_widget.set_action(song_delete, i)

            reload_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnreload.png", [0,0], [0.05, 0.05 * self.window_ratio]))
            reload_widget.set_action(song_reload, i)

            track_display_widget = self.menus[Menus.SONGS].add_widget(None, self.font)
            track_display_widget.set_text(get_track_display_text(song), 9, [0,0])
            track_display_widget.set_text_colour([0.7] * 4)

            track_button_size = 0.035
            track_down_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnback.png", [0,0], [track_button_size, track_button_size * self.window_ratio]))
            track_down_widget.set_action(song_track_down, i)

            track_up_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnback.png", [0,0], [-track_button_size, track_button_size * self.window_ratio]))
            track_up_widget.set_action(song_track_up, i)

            self.song_widgets.append({
                "play": play_widget,
                "score": score_widget,
                "delete": delete_widget,
                "reload": reload_widget,
                "track_up": track_up_widget,
                "track_down": track_down_widget,
                "track_display": track_display_widget,
            })

        self._set_song_menu_pos()

        menu_row = 0.8
        menu_thirds = 2.0 / 4
        menu_item_size = [0.31, 0.18]
        self.menus[Menus.SONGS].add_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", [0.7, 0.5, 0.7, 0.6], [0.0, menu_row], [2.0, 0.5])
        )

        btn_devices = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btn_devices.png", [-1.0 + menu_thirds * 1, menu_row], menu_item_size))
        btn_devices.set_action(self.show_dialog, Dialogs.DEVICES)
        self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btn_options.png", [-1.0 + menu_thirds * 2, menu_row], menu_item_size))
        btn_quit = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btn_quit.png", [-1.0 + menu_thirds * 3, menu_row], menu_item_size))
        btn_quit.set_action(quit, self)

        def set_devices_input(dir:int):
            devices = self.devices.input_devices
            cur_device_id = devices.index(self.devices.input_device_name)
            cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
            self.devices.input_device_name = devices[cur_device_id]
            self.device_input_widget.set_text(self.devices.input_device_name, 10, [-0.05,0.3])
            self.songbook.input_device = self.devices.input_device_name

        def get_device_input_dir(dir:int) -> bool:
            devices = self.devices.input_devices
            cur_device_id = devices.index(self.devices.input_device_name)
            return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)

        def get_device_input_col(dir) -> list:
            return [1.0] * 4 if get_device_input_dir(dir) else [0.4] * 4

        def set_devices_output(dir):
            devices = self.devices.output_devices
            cur_device_id = devices.index(self.devices.output_device_name)
            cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
            self.devices.output_device_name = devices[cur_device_id]
            self.device_output_widget.set_text(self.devices.output_device_name, 10, [-0.05,0.2])
            self.songbook.output_device = self.devices.output_device_name

        def get_device_output_dir(dir:int) -> bool:
            devices = self.devices.output_devices
            cur_device_id = devices.index(self.devices.output_device_name)
            return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)

        def get_device_output_col(dir) -> list:
            return [1.0] * 4 if get_device_output_dir(dir) else [0.4] * 4

        def devices_refresh(sleep_delay_ms: int):
            self.devices.refresh_io()

        def devices_output_test(args):
            self.devices.output_test()

            
        # Add device params
        device_button_size = 0.035
        input_label = self.dialogs[Dialogs.DEVICES].add_widget(None, self.font)
        input_label.set_text(f"Input ", 10, [-0.3,0.3])
        input_label.set_text_colour([0.7] * 4)

        self.device_input_widget = self.dialogs[Dialogs.DEVICES].add_widget(None, self.font)
        self.device_input_widget.set_text(self.devices.input_device_name, 8, [-0.05,0.3])
        self.device_input_widget.set_text_colour([0.9] * 4)

        input_down = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/btnback.png", [-0.1,0.315], [device_button_size, device_button_size * self.window_ratio]))
        input_down.set_action(set_devices_input, -1)
        input_down.set_colour_func(get_device_input_col, -1)

        input_up = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/btnback.png", [0.35,0.315], [-device_button_size, device_button_size * self.window_ratio]))
        input_up.set_action(set_devices_input, 1)
        input_up.set_colour_func(get_device_input_col, 1)

        output_label = self.dialogs[Dialogs.DEVICES].add_widget(None, self.font)
        output_label.set_text(f"Output: ", 10, [-0.3, 0.2])
        output_label.set_text_colour([0.7] * 4)

        self.device_output_widget = self.dialogs[Dialogs.DEVICES].add_widget(None, self.font)
        self.device_output_widget.set_text(self.devices.output_device_name, 8, [-0.05,0.2])
        self.device_output_widget.set_text_colour([0.9] * 4)

        output_down = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/btnback.png", [-0.1,0.215], [device_button_size, device_button_size * self.window_ratio]))
        output_down.set_action(set_devices_output, -1)
        output_down.set_colour_func(get_device_output_col, -1)

        output_up = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/btnback.png", [0.35,0.215], [-device_button_size, device_button_size * self.window_ratio]))
        output_up.set_action(set_devices_output, 1)
        output_up.set_colour_func(get_device_output_col, 1)

        self.devices_apply = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/panel.tga", [0.2,-0.2], [0.2, 0.08 * self.window_ratio]), self.font)
        self.devices_apply.set_text(f"Reconnect", 11, [-0.07, -0.015])
        self.devices_apply.set_text_colour([0.9] * 4)
        self.devices_apply.set_action(devices_refresh, 0)

        self.devices_test = self.dialogs[Dialogs.DEVICES].add_widget(self.textures.create_sprite_texture("gui/panel.tga", [-0.2,-0.2], [0.25, 0.08 * self.window_ratio]), self.font)
        self.devices_test.set_text(f"Test Output", 11, [-0.1, -0.015])
        self.devices_test.set_text_colour([0.9] * 4)
        self.devices_test.set_action(devices_output_test, 0)


    def update(self, dt: float, music_running: bool):
        """Element specific per-frame updates"""
        input, draw = self.is_menu_active(Menus.GAME)
        if input or draw:
            for _, (type, menu) in enumerate(self.elements.items()):
                if self.is_menu_active(type):
                    for _, (name, widget) in enumerate(menu.items()):
                        if menu is Menus.GAME:
                            if name == "bg": widget.draw(dt if music_running else dt * 0.1)
                            if name == "note_bg_btm": widget.sprite.set_colour(self.note_correct_colour)
                            if name == "note_bg_top": widget.sprite.set_colour(self.note_correct_colour)
                            self.note_correct_colour = [max(0.65, i - 0.5 * dt) for index, i in enumerate(self.note_correct_colour) if index <= 3]
        
        input, draw = self.is_menu_active(Menus.SONGS)
        if input or draw:
            self.song_scroll = lerp(self.song_scroll, self.song_scroll_target, dt * 5.0)
            if abs(self.song_scroll - self.song_scroll_target) > 0.01:
                scroll_max = len(self.song_widgets) * Menu.SONG_SPACING
                self.scroll_widget.set_pos([0.9, 0.73 - (1.44 * (self.song_scroll / scroll_max))])
                self._set_song_menu_pos()


    def set_event(self, name:str):
        """Element specific per-event updates"""
        if name == "score_vfx":
            self.note_correct_colour = [1.0 for index, i in enumerate(self.note_correct_colour) if index <= 3]            


    def transition(self, tfrom: Menus, tto: Menus):
        self.menus[tfrom].set_active(False, False)
        self.menus[tto].set_active(True, True)


    def get_menu(self, type: Menus):
        return self.menus[type]

    
    def is_menu_active(self, type: Menus):
        menu_input, menu_draw = self.menus[type].is_active()
        if self.is_any_dialog_active():
            return False, menu_draw
        return menu_input, menu_draw

    
    def is_any_dialog_active(self):
        return False


    def is_dialog_active(self, type: Dialogs):
        return False


    def show_dialog(self, type: Dialogs):
        self.dialogs[type].set_active(True, True)


    def hide_dialog(self, type: Dialogs):
        self.dialogs[type].set_active(False, False)

