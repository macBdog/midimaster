from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.gui import Gui
from gamejam.input import Input
from gamejam.settings import GameSettings
from gamejam.quickmaff import lerp

from staff import Staff
from midi_devices import MidiDevices
from scrolling_background import ScrollingBackground
from menu_func import (
    SONG_SPACING, DIALOG_COLOUR,
    Menus, Dialogs,
    song_play, song_reload, song_delete, song_track_up, song_track_down, song_list_scroll,
    get_track_display_text,
    set_devices_input, get_device_input_col, 
    set_devices_output, get_device_output_col,
    devices_refresh, devices_output_test, set_devices_output,
    get_device_output_col, devices_refresh, devices_output_test,
    menu_quit, menu_transition,
)


class Menu():
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

        self.input.cursor.set_sprite(self.textures.create_sprite_texture("gui/cursor.png", Coord2d(), Coord2d(0.25, 0.25 * self.window_ratio)))

        # Create sub-guis for each screen of the game, starting with active splash screen
        self.menus[Menus.SPLASH] = Gui("splash_screen", self.graphics, gui.debug_font, False)
        self.menus[Menus.SPLASH].set_active(True, True)
        self.menus[Menus.SPLASH].add_create_widget(self.textures.create_sprite_texture("splash_background.png", Coord2d(), Coord2d(2.0, 2.0)))
        gui.add_child(self.menus[Menus.SPLASH])

        self.menus[Menus.SONGS] = Gui("menu_screen", self.graphics, gui.debug_font, False)
        self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/menu_bg.png", Coord2d(), Coord2d(2.0, 2.0)))
        gui.add_child(self.menus[Menus.SONGS])

        splash_anim_time = 0.15 if GameSettings.DEV_MODE else 2.0
        splash_destination = Menus.GAME if GameSettings.DEV_MODE else Menus.SONGS
        title = self.menus[Menus.SPLASH].add_create_widget(name="splash_title", sprite=self.textures.create_sprite_texture("gui/imgtitle.tga", Coord2d(), Coord2d(0.6, 0.6)))
        title.animate(AnimType.FadeInOutSmooth, splash_anim_time)
        title.animation.set_action(splash_anim_time, menu_transition, {"menu": self, "from": Menus.SPLASH, "to": splash_destination})
        self._set_elem(Menus.SPLASH, "title", title)
        
        game_bg_pos_x = Staff.Pos[0] + Staff.Width * 0.5
        self.menus[Menus.GAME] = Gui("game_screen", self.graphics, gui.debug_font, False)
        self.menus[Menus.GAME].add_create_widget(self.textures.create_sprite_texture("game_background.tga", Coord2d(), Coord2d(2.0, 2.0)))
        self.menus[Menus.GAME].add_create_widget(self.textures.create_sprite_shape([0.5] * 4, Coord2d(game_bg_pos_x, Staff.Pos[1] + Staff.StaffSpacing * 2.0), Coord2d(Staff.Width, Staff.StaffSpacing * 4.0)))
        gui.add_child(self.menus[Menus.GAME])

        bg_size_top = 0.65
        bg_size_btm = 1.25
        note_bg_top = self.menus[Menus.GAME].add_create_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, Coord2d(game_bg_pos_x, Staff.Pos[1] + (Staff.StaffSpacing * 4.0) + (bg_size_top * 0.5)), Coord2d(Staff.Width, bg_size_top * -1.0))
        )
        note_bg_btm = self.menus[Menus.GAME].add_create_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", self.note_correct_colour, Coord2d(game_bg_pos_x, Staff.Pos[1] - bg_size_btm * 0.5), Coord2d(Staff.Width, bg_size_btm))
        )
        self._set_elem(Menus.GAME, "note_bg_top", note_bg_top)
        self._set_elem(Menus.GAME, "note_bg_btm", note_bg_btm)
        self._set_elem(Menus.GAME, "bg", ScrollingBackground(self.graphics, self.textures, "menu_glyphs.tga"))

        # Create the dialogs
        dialog_size = Coord2d(0.8, 1.1)
        self.dialogs[Dialogs.DEVICES] = Gui("devices", self.graphics, gui.debug_font, False)
        self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_shape(DIALOG_COLOUR, Coord2d(), dialog_size))
        delete_widget = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/checkboxon.tga", Coord2d(dialog_size.x * 0.5, dialog_size.y * 0.5), Coord2d(0.05, 0.05 * self.window_ratio)))
        delete_widget.set_action(self.hide_dialog, {"menu": self, "type": Dialogs.DEVICES})
        gui.add_child(self.dialogs[Dialogs.DEVICES])     
        

    def _get_elem(self, menu: Menus, name: str):
        return self.elements[menu][name]


    def _set_elem(self, menu: Menus, name: str, widget):
        self.elements[menu][name] = widget


    def _set_album_menu_pos(self):
        num_items = self.songbook.get_num_albums()
        for i in range(num_items):
            item_pos = Coord2d(-0.333, (0.4 - i * SONG_SPACING) + self.song_scroll)
            track_pos = Coord2d(item_pos.x + 0.125, item_pos.y - 0.1)
            widgets_for_song = self.song_widgets[i]
            widgets_for_song["play"].set_offset(item_pos)
            widgets_for_song["delete"].set_offset(Coord2d(item_pos.x-0.09, item_pos.y))
            widgets_for_song["reload"].set_offset(Coord2d(item_pos.x-0.14, item_pos.y))
            widgets_for_song["score"].set_offset(Coord2d(item_pos.x + 0.75, item_pos.y))
            widgets_for_song["track_display"].set_offset(Coord2d(track_pos.x, track_pos.y))
            widgets_for_song["track_down"].set_offset(Coord2d(track_pos.x - 0.02, track_pos.y + 0.02))
            widgets_for_song["track_up"].set_offset(Coord2d(track_pos.x + 0.3, track_pos.y + 0.02))


    def prepare(self, font, music, songbook):
        self.font = font
        self.music = music
        self.songbook = songbook

        # Scroll indicator for song list
        self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_shape([0.1, 0.1, 0.1, 0.5], Coord2d(0.9, 0.0), Coord2d(0.05, 1.6)))
        self.scroll_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/sliderknob.png", Coord2d(0.9, 0.73), Coord2d(0.035, 0.035 * self.window_ratio)))
        scroll_up_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btnup.png", Coord2d(0.9, 0.8), Coord2d(0.05, 0.05 * self.window_ratio)))
        scroll_up_widget.set_action(song_list_scroll, {"menu":self, "dir":-0.333})
        scroll_down_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btnup.png", Coord2d(0.9,-0.8), Coord2d(0.05, -0.05 * self.window_ratio)))
        scroll_down_widget.set_action(song_list_scroll, {"menu":self, "dir":0.333})
        self.input.add_scroll_mapping(song_list_scroll, {"menu":self})

        num_albums = self.songbook.get_num_albums()
        for i in range(num_albums):
            album = self.songbook.get_album(i)

            play_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btnplay.tga", Coord2d(), Coord2d(0.125, 0.1)), self.font)
            play_widget.set_text(song.get_name(), 12, Coord2d(0.08, -0.02))
            play_widget.set_text_colour([0.85, 0.85, 0.85, 0.85])
            play_widget.set_action(song_play, {"menu":self, "song_id":i})

            performance_score = 0
            score_widget = self.menus[Menus.SONGS].add_create_text_widget(self.font, f"{round((performance_score / song.get_max_score()) * 100.0, 1)}%", 14)

            delete_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btntrash.png", Coord2d(), Coord2d(0.05, 0.05 * self.window_ratio)))
            delete_widget.set_action(song_delete, {"menu":self, "song_id":i})

            reload_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btnreload.png", Coord2d(), Coord2d(0.05, 0.05 * self.window_ratio)))
            reload_widget.set_action(song_reload, {"menu": self, "song_id":i})

            song = album.songbook.get_song(0)
            track_display_widget = self.menus[Menus.SONGS].add_create_text_widget(self.font, get_track_display_text(song), 9)
            track_display_widget.set_text_colour([0.7] * 4)

            track_button_size = 0.035
            track_down_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btnback.png", Coord2d(), Coord2d(track_button_size, track_button_size * self.window_ratio)))
            track_down_widget.set_action(song_track_down, {"menu": self, "song_id":i})

            track_up_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btnback.png", Coord2d(0.0,0.0), Coord2d(-track_button_size, track_button_size * self.window_ratio)))
            track_up_widget.set_action(song_track_up, {"menu": self, "song_id":i})

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
        menu_item_size = Coord2d(0.31, 0.18)
        self.menus[Menus.SONGS].add_create_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", [0.7, 0.5, 0.7, 0.6], Coord2d(0.0, menu_row), Coord2d(2.0, 0.5))
        )

        btn_devices = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btn_devices.png", Coord2d(-1.0 + menu_thirds * 1, menu_row), menu_item_size))
        btn_devices.set_action(self.show_dialog, {"menu": self, "type": Dialogs.DEVICES})
        self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btn_options.png", Coord2d(-1.0 + menu_thirds * 2, menu_row), menu_item_size))
        btn_quit = self.menus[Menus.SONGS].add_create_widget(self.textures.create_sprite_texture("gui/btn_quit.png", Coord2d(-1.0 + menu_thirds * 3, menu_row), menu_item_size))
        btn_quit.set_action(menu_quit, {"menu": self})
            
        # Add device params
        device_button_size = 0.035
        input_label = self.dialogs[Dialogs.DEVICES].add_create_text_widget(self.font, f"Input ", 10, Coord2d(-0.3, 0.3))
        input_label.set_text_colour([0.7] * 4)

        self.device_input_widget = self.dialogs[Dialogs.DEVICES].add_create_text_widget(self.font, self.devices.input_device_name, 8, Coord2d(-0.05, 0.3))
        self.device_input_widget.set_text_colour([0.9] * 4)

        input_down = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/btnback.png", Coord2d(-0.1,0.315), Coord2d(device_button_size, device_button_size * self.window_ratio)))
        input_down.set_action(set_devices_input, {"menu":self, "dir":-1})
        input_down.set_colour_func(get_device_input_col, {"menu":self, "dir":-1})

        input_up = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/btnback.png", Coord2d(0.35,0.315), Coord2d(-device_button_size, device_button_size * self.window_ratio)))
        input_up.set_action(set_devices_input, {"menu":self, "dir":1})
        input_up.set_colour_func(get_device_input_col, {"menu":self, "dir":1})

        output_label = self.dialogs[Dialogs.DEVICES].add_create_text_widget(self.font, f"Output: ", 10, Coord2d(-0.3, 0.2))
        output_label.set_text_colour([0.7] * 4)

        self.device_output_widget = self.dialogs[Dialogs.DEVICES].add_create_text_widget(self.font, self.devices.output_device_name, 8, Coord2d(-0.05, 0.2))
        self.device_output_widget.set_text_colour([0.9] * 4)

        output_down = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/btnback.png", Coord2d(-0.1,0.215), Coord2d(device_button_size, device_button_size * self.window_ratio)))
        output_down.set_action(set_devices_output, {"menu":self, "dir":-1})
        output_down.set_colour_func(get_device_output_col, {"menu":self, "dir":-1})

        output_up = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/btnback.png", Coord2d(0.35,0.215), Coord2d(-device_button_size, device_button_size * self.window_ratio)))
        output_up.set_action(set_devices_output, {"menu":self, "dir":1})
        output_up.set_colour_func(get_device_output_col, {"menu":self, "dir":1})

        self.devices_apply = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/panel.tga", Coord2d(0.2,-0.2), Coord2d(0.2, 0.08 * self.window_ratio)), self.font)
        self.devices_apply.set_text(f"Reconnect", 11, Coord2d(-0.07, -0.015))
        self.devices_apply.set_text_colour([0.9] * 4)
        self.devices_apply.set_action(devices_refresh, {"menu":self})

        self.devices_test = self.dialogs[Dialogs.DEVICES].add_create_widget(self.textures.create_sprite_texture("gui/panel.tga", Coord2d(-0.2,-0.2), Coord2d(0.25, 0.08 * self.window_ratio)), self.font)
        self.devices_test.set_text(f"Test Output", 11, Coord2d(-0.1, -0.015))
        self.devices_test.set_text_colour([0.9] * 4)
        self.devices_test.set_action(devices_output_test, {"menu":self})


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
                scroll_max = len(self.song_widgets) * SONG_SPACING
                self.scroll_widget.set_offset(Coord2d(0.9, 0.73 - (1.44 * (self.song_scroll / scroll_max))))
                self._set_album_menu_pos()


    def set_event(self, name:str):
        """Element specific per-event updates"""
        if name == "score_vfx":
            self.note_correct_colour = [1.0 for index, i in enumerate(self.note_correct_colour) if index <= 3]            


    def transition(self, from_menu: Menus, to_menu: Menus):
        self.menus[from_menu].set_active(False, False)
        self.menus[to_menu].set_active(True, True)


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


    def show_dialog(self, **kwargs):
        menu = kwargs["menu"]
        type = kwargs["type"]
        menu.dialogs[type].set_active(True, True)


    def hide_dialog(self, **kwargs):
        menu = kwargs["menu"]
        type = kwargs["type"]
        menu.dialogs[type].set_active(False, False)

