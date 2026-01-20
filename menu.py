from dataclasses import dataclass
from typing import List, Tuple

from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.gui import Gui
from gamejam.graphics import Graphics
from gamejam.input import Input
from gamejam.settings import GameSettings
from gamejam.quickmaff import lerp
from gamejam.texture import TextureManager
from gamejam.widget import Widget
from gamejam.font import Font

from notes import Notes
from staff import Staff
from midi_devices import MidiDevices
from scrolling_background import ScrollingBackground
from menu_func import (
    ALBUM_SPACING, SONG_SPACING, DIALOG_COLOUR,
    MusicMode, Menus, Dialogs,
    song_play, song_reload, song_delete, song_track_up, song_track_down, song_list_scroll,
    get_track_display_text,
    set_devices_input, get_device_input_col, 
    set_devices_output, get_device_output_col,
    devices_refresh, devices_output_test, set_devices_output,
    get_device_output_col, devices_refresh, devices_output_test,
    menu_quit, menu_transition,
)


# Configuration Constants
class MenuConfig:
    """Centralized configuration for menu layout and styling"""
    # Button sizes
    SMALL_BUTTON_SIZE = 0.035
    MEDIUM_BUTTON_SIZE = 0.05
    TRACK_BUTTON_SIZE = 0.035
    
    # Menu positioning
    MENU_ROW_Y = 0.8
    MENU_ITEM_SIZE = Coord2d(0.31, 0.18)
    
    # Colors
    TEXT_COLOR_BRIGHT = [0.9] * 4
    TEXT_COLOR_NORMAL = [0.85] * 4
    TEXT_COLOR_DIM = [0.7] * 4
    
    # Splash screen
    SPLASH_ANIM_TIME_DEV = 0.15
    SPLASH_ANIM_TIME_NORMAL = 2.0
    
    # Game background
    GAME_BG_COLOR = [0.5] * 4
    NOTE_BG_SIZE_TOP = 0.65
    NOTE_BG_SIZE_BTM = 1.25
    
    # Device dialog
    DEVICE_DIALOG_SIZE = Coord2d(0.8, 1.1)
    DEVICE_INPUT_Y = 0.3
    DEVICE_OUTPUT_Y = 0.2
    DEVICE_NOTE_INPUT_Y = 0.1
    DEVICE_BUTTON_SPACING = 0.4  # Horizontal spacing between left and right buttons
    
    # Game over dialog
    GAME_OVER_DIALOG_SIZE = Coord2d(0.7, 0.9)


class WidgetFactory:
    """Helper class for creating GUI widgets with less boilerplate"""
    
    @staticmethod
    def create_button(gui: Gui, textures: TextureManager, texture_path: str, 
                      pos: Coord2d, size: Coord2d, action=None, action_args=None,
                      font: Font = None, text: str = None, text_size: int = 11,
                      text_offset: Coord2d = None, color_func=None, color_func_args=None) -> Widget:
        """Create a button widget with texture, action, and optional text"""
        widget = gui.add_create_widget(textures.create(texture_path, pos, size), font)

        if action:
            widget.set_action(action, action_args or {})

        if color_func:
            widget.set_colour_func(color_func, color_func_args or {})

        if text:
            offset = text_offset or Coord2d()
            widget.set_text(text, text_size, offset)
        
        return widget
    
    @staticmethod
    def create_text(gui: Gui, font: Font, text: str, size: int, 
                    pos: Coord2d = None, color: list = None) -> Widget:
        """Create a text widget with font, text, and color"""
        widget = gui.add_create_text_widget(font, text, size, pos)
        
        if color:
            widget.set_text_colour(color)
        
        return widget
    
    @staticmethod
    def create_button_pair(gui: Gui, textures: TextureManager, window_ratio: float,
                          texture_prev: str, texture_next: str,
                          base_pos: Coord2d, size: float,
                          action_prev, action_args_prev: dict,
                          action_next, action_args_next: dict,
                          width: float = 0.1, height: float = 0.0,
                          color_func_prev=None, color_func_next=None) -> Tuple[Widget, Widget]:
        """Create a pair of navigation buttons (prev/next, up/down, etc.)"""
        button_size = Coord2d(size, size * window_ratio)
        pos_prev = Coord2d(base_pos.x - width, base_pos.y + height)
        widget_prev = WidgetFactory.create_button(
            gui, textures, texture_prev, pos_prev, button_size,
            action_prev, action_args_prev,
            color_func=color_func_prev, color_func_args=action_args_prev
        )

        pos_next = Coord2d(base_pos.x + width, base_pos.y - height)
        widget_next = WidgetFactory.create_button(
            gui, textures, texture_next, pos_next, button_size,
            action_next, action_args_next,
            color_func=color_func_next, color_func_args=action_args_next
        )
        return widget_prev, widget_next

    @staticmethod
    def create_dialog_background(gui: Gui, textures: TextureManager,
                                 size: Coord2d, color: list = None) -> Widget:
        """Create a dialog background widget"""
        bg_color = color or DIALOG_COLOUR
        return gui.add_create_widget(textures.create(None, Coord2d(), size, bg_color))


@dataclass(init=False)
class SongWidget:
    play: Widget
    score: Widget
    delete: Widget
    reload: Widget
    track_up: Widget
    track_down: Widget
    track_display: Widget


@dataclass()
class AlbumWidget:
    name: Widget
    songs: List[SongWidget]


# Pos and size of song selection scroll bar
SONG_SCRL_PX = 0.9
SONG_SCRL_PY = -0.2
SONG_SCRL_SX = 0.05
SONG_SCRL_SY = 1.4
SONG_SCRL_H = SONG_SCRL_SY - SONG_SCRL_SX * 3


class Menu():
    """Utility class to separate all the gui element drawing from main game logic."""
    def __init__(self, graphics: Graphics, input: Input, gui: Gui, devices: MidiDevices, width: int, height: int, textures: TextureManager):
        self.menus: dict[Gui] = {}
        self.dialogs: dict[Gui] = {}
        self.elements = {m:{} for m in Menus}
        self.graphics = graphics
        self.input = input
        self.devices = devices
        self.window_width = width
        self.window_height = height
        self.window_ratio = width / height
        self.textures = textures
        self.song_albums: list[AlbumWidget] = []
        self.song_scroll = 0.0
        self.song_scroll_target = 0.0
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.75]
        self.running = True
        self.dialog_overlay = None

        self.input.cursor.set_sprite(self.textures.create_sprite_texture("gui/cursor.png", Coord2d(), Coord2d(0.25, 0.25 * self.window_ratio)))

        # Create sub-guis for each screen
        self._create_splash_menu(gui)
        self._create_songs_menu(gui)
        self._create_game_menu(gui)
        self._create_dialog_overlay(gui)
        self._create_dialogs(gui)


    def _create_splash_menu(self, parent_gui: Gui):
        """Create and configure the splash screen menu"""
        self.menus[Menus.SPLASH] = Gui("splash_screen", self.graphics, parent_gui.debug_font, False)
        parent_gui.add_child(self.menus[Menus.SPLASH])
        
        self.menus[Menus.SPLASH].set_active(True, True)
        self.menus[Menus.SPLASH].add_create_widget(self.textures.create("splash_background.png", Coord2d(), Coord2d(2.0, 2.0)))
        
        splash_anim_time = MenuConfig.SPLASH_ANIM_TIME_DEV if GameSettings.DEV_MODE else MenuConfig.SPLASH_ANIM_TIME_NORMAL
        splash_destination = Menus.GAME if GameSettings.DEV_MODE else Menus.SONGS
        title = self.menus[Menus.SPLASH].add_create_widget(name="splash_title", sprite=self.textures.create_sprite_texture("gui/imgtitle.tga", Coord2d(), Coord2d(0.6, 0.6)))
        title.animate(AnimType.FadeInOutSmooth, splash_anim_time)
        title.animation.set_action(splash_anim_time, menu_transition, {"menu": self, "from": Menus.SPLASH, "to": splash_destination})
        self._set_elem(Menus.SPLASH, "title", title)
    
    def _create_songs_menu(self, parent_gui: Gui):
        """Create and configure the songs menu"""
        self.menus[Menus.SONGS] = Gui("menu_screen", self.graphics, parent_gui.debug_font, False)
        parent_gui.add_child(self.menus[Menus.SONGS])
        self.menus[Menus.SONGS].add_create_widget(self.textures.create("gui/menu_bg.png", Coord2d(), Coord2d(2.0, 2.0)))

    def _create_game_menu(self, parent_gui: Gui):
        """Create and configure the game screen menu"""
        game_bg_pos_x = Staff.Pos[0] + Staff.Width * 0.5
        self.menus[Menus.GAME] = Gui("game_screen", self.graphics, parent_gui.debug_font, False)
        self.menus[Menus.GAME].add_create_widget(self.textures.create("game_background.tga", Coord2d(), Coord2d(2.0, 2.0)))
        self.menus[Menus.GAME].add_create_widget(self.textures.create(None, Coord2d(game_bg_pos_x, Staff.Pos[1] + Staff.StaffSpacing * 2.0), Coord2d(Staff.Width, Staff.StaffSpacing * 4.0), MenuConfig.GAME_BG_COLOR))
        parent_gui.add_child(self.menus[Menus.GAME])
        
        # Add note background gradients
        note_bg_top = self.menus[Menus.GAME].add_create_widget(
            self.textures.create("vgradient.png", Coord2d(game_bg_pos_x, Staff.Pos[1] + (Staff.StaffSpacing * 4.0) + (MenuConfig.NOTE_BG_SIZE_TOP * 0.5)), Coord2d(Staff.Width, MenuConfig.NOTE_BG_SIZE_TOP * -1.0), self.note_correct_colour)
        )
        note_bg_btm = self.menus[Menus.GAME].add_create_widget(
            self.textures.create("vgradient.png", Coord2d(game_bg_pos_x, Staff.Pos[1] - MenuConfig.NOTE_BG_SIZE_BTM * 0.5), Coord2d(Staff.Width, MenuConfig.NOTE_BG_SIZE_BTM), self.note_correct_colour)
        )
        self._set_elem(Menus.GAME, "note_bg_top", note_bg_top)
        self._set_elem(Menus.GAME, "note_bg_btm", note_bg_btm)
        self._set_elem(Menus.GAME, "bg", ScrollingBackground(self.graphics, self.textures, "menu_glyphs.tga"))

    def _create_dialogs(self, parent_gui: Gui):
        """Create and configure all dialog windows"""
        # Devices dialog
        self.dialogs[Dialogs.DEVICES] = Gui("devices", self.graphics, parent_gui.debug_font, False)
        WidgetFactory.create_dialog_background(self.dialogs[Dialogs.DEVICES], self.textures, MenuConfig.DEVICE_DIALOG_SIZE)
        close_button_size = Coord2d(MenuConfig.MEDIUM_BUTTON_SIZE, MenuConfig.MEDIUM_BUTTON_SIZE * self.window_ratio)
        close_button_pos = Coord2d(MenuConfig.DEVICE_DIALOG_SIZE.x * 0.5, MenuConfig.DEVICE_DIALOG_SIZE.y * 0.5)
        WidgetFactory.create_button(
            self.dialogs[Dialogs.DEVICES], self.textures, "gui/checkboxon.tga",
            close_button_pos, close_button_size,
            self.hide_dialog, {"menu": self, "type": Dialogs.DEVICES}
        )
        parent_gui.add_child(self.dialogs[Dialogs.DEVICES])

        # Game over dialog
        self.dialogs[Dialogs.GAME_OVER] = Gui("game_over", self.graphics, parent_gui.debug_font, False)
        WidgetFactory.create_dialog_background(self.dialogs[Dialogs.GAME_OVER], self.textures, MenuConfig.GAME_OVER_DIALOG_SIZE)
        parent_gui.add_child(self.dialogs[Dialogs.GAME_OVER])
    
    def _create_dialog_overlay(self, parent_gui: Gui):
        """Create a semi-transparent full-screen overlay that darkens the screen when dialogs are active"""
        self.dialog_overlay = parent_gui.add_create_widget(
            self.textures.create_sprite_shape([0.0, 0.0, 0.0, 0.4], Coord2d(0.0, 0.0), Coord2d(2.0, 2.0))
        )
        self.dialog_overlay.set_disabled(True)

    def _get_elem(self, menu: Menus, name: str):
        return self.elements[menu][name]

    def _set_elem(self, menu: Menus, name: str, widget):
        self.elements[menu][name] = widget
    
    def _create_song_widget(self, album, song) -> SongWidget:
        """Create all widgets for a single song entry"""
        song_widget = SongWidget()
        button_size = Coord2d(MenuConfig.MEDIUM_BUTTON_SIZE, MenuConfig.MEDIUM_BUTTON_SIZE * self.window_ratio)
        
        # Play button with text
        song_widget.play = WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btnplay.tga",
            Coord2d(), Coord2d(0.125, 0.1),
            song_play, {"menu": self, "song": song},
            font=self.font
        )
        song_widget.play.set_text_colour(MenuConfig.TEXT_COLOR_NORMAL)
        
        # Score display
        song_widget.score = WidgetFactory.create_text(
            self.menus[Menus.SONGS], self.font,
            self.get_song_score_text(song), 14
        )
        
        # Delete and reload buttons
        song_widget.delete = WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btntrash.png",
            Coord2d(), button_size,
            song_delete, {"menu": self, "album": album, "song": song, "widget": song_widget}
        )
        
        song_widget.reload = WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btnreload.png",
            Coord2d(), button_size,
            song_reload, {"menu": self, "album": album, "song": song}
        )
        
        # Track display and navigation buttons
        song_widget.track_display = WidgetFactory.create_text(
            self.menus[Menus.SONGS], self.font,
            get_track_display_text(song), 9,
            color=MenuConfig.TEXT_COLOR_DIM
        )
        
        song_widget.track_down, song_widget.track_up = WidgetFactory.create_button_pair(
            self.menus[Menus.SONGS], self.textures, self.window_ratio,
            "gui/btnback.png", "gui/btnnext.png",
            Coord2d(), MenuConfig.TRACK_BUTTON_SIZE,
            song_track_down, {"widget": song_widget.track_display, "song": song},
            song_track_up, {"widget": song_widget.track_display, "song": song},
            width=0.16, height=0.0
        )
        
        return song_widget

    def _setup_device_dialog(self):
        """Setup all widgets for the device configuration dialog"""
        WidgetFactory.create_text(
            self.dialogs[Dialogs.DEVICES], self.font,
            "Input ", 10, Coord2d(-0.3, MenuConfig.DEVICE_INPUT_Y),
            color=MenuConfig.TEXT_COLOR_BRIGHT
        )

        self.device_input_widget = WidgetFactory.create_text(
            self.dialogs[Dialogs.DEVICES], self.font,
            self.devices.input_device_name, 8, Coord2d(-0.05, MenuConfig.DEVICE_INPUT_Y),
            color=MenuConfig.TEXT_COLOR_BRIGHT
        )

        WidgetFactory.create_button_pair(
            self.dialogs[Dialogs.DEVICES], self.textures, self.window_ratio,
            "gui/btnback.png", "gui/btnnext.png",
            Coord2d(0.12, MenuConfig.DEVICE_INPUT_Y + 0.015), MenuConfig.SMALL_BUTTON_SIZE,
            set_devices_input, {"menu": self, "dir": -1},
            set_devices_input, {"menu": self, "dir": 1},
            width=0.2, height=0.0,
            color_func_prev=get_device_input_col,
            color_func_next=get_device_input_col
        )

        # Output device section
        WidgetFactory.create_text(
            self.dialogs[Dialogs.DEVICES], self.font,
            "Output: ", 10, Coord2d(-0.3, MenuConfig.DEVICE_OUTPUT_Y),
            color=MenuConfig.TEXT_COLOR_DIM
        )

        self.device_output_widget = WidgetFactory.create_text(
            self.dialogs[Dialogs.DEVICES], self.font,
            self.devices.output_device_name, 8, Coord2d(-0.05, MenuConfig.DEVICE_OUTPUT_Y),
            color=MenuConfig.TEXT_COLOR_BRIGHT
        )

        WidgetFactory.create_button_pair(
            self.dialogs[Dialogs.DEVICES], self.textures, self.window_ratio,
            "gui/btnback.png", "gui/btnnext.png",
            Coord2d(0.12, MenuConfig.DEVICE_OUTPUT_Y + 0.015), MenuConfig.SMALL_BUTTON_SIZE,
            set_devices_output, {"menu": self, "dir": -1},
            set_devices_output, {"menu": self, "dir": 1},
            width=0.2, height=0.0,
            color_func_prev=get_device_output_col,
            color_func_next=get_device_output_col
        )

        # Note input display
        WidgetFactory.create_text(
            self.dialogs[Dialogs.DEVICES], self.font,
            "Note Input: ", 10, Coord2d(-0.3, MenuConfig.DEVICE_NOTE_INPUT_Y),
            color=MenuConfig.TEXT_COLOR_DIM
        )

        self.device_note_input_widget = WidgetFactory.create_text(
            self.dialogs[Dialogs.DEVICES], self.font,
            "N/A", 8, Coord2d(-0.05, MenuConfig.DEVICE_NOTE_INPUT_Y),
            color=MenuConfig.TEXT_COLOR_BRIGHT
        )

        # Action buttons
        self.devices_apply = WidgetFactory.create_button(
            self.dialogs[Dialogs.DEVICES], self.textures, "gui/panel.tga",
            Coord2d(0.2, -0.2), Coord2d(0.2, 0.08 * self.window_ratio),
            devices_refresh, {"menu": self},
            font=self.font, text="Reconnect", text_size=11,
            text_offset=Coord2d(-0.07, -0.015)
        )
        self.devices_apply.set_text_colour(MenuConfig.TEXT_COLOR_BRIGHT)
        
        self.devices_test = WidgetFactory.create_button(
            self.dialogs[Dialogs.DEVICES], self.textures, "gui/panel.tga",
            Coord2d(-0.2, -0.2), Coord2d(0.25, 0.08 * self.window_ratio),
            devices_output_test, {"menu": self},
            font=self.font, text="Test Output", text_size=11,
            text_offset=Coord2d(-0.1, -0.015)
        )
        self.devices_test.set_text_colour(MenuConfig.TEXT_COLOR_BRIGHT)


    def _set_album_menu_pos(self):
        cutoff = 0.55
        item_pos = Coord2d(-0.5, self.song_scroll+0.25)
        for album_widget in self.song_albums:
            item_pos.x = -0.5
            album_widget.name.set_offset(Coord2d(item_pos.x, item_pos.y))
            album_widget.name.set_disabled(item_pos.y < -1.0 or item_pos.y > cutoff)
            item_pos.y -= SONG_SPACING * 0.5
            item_pos.x = -0.3

            for song_widget in album_widget.songs:
                track_pos = Coord2d(item_pos.x+0.125, item_pos.y-0.1)
                song_widget.play.set_offset(Coord2d(item_pos.x, item_pos.y))
                song_widget.delete.set_offset(Coord2d(item_pos.x-0.09, item_pos.y))
                song_widget.reload.set_offset(Coord2d(item_pos.x-0.14, item_pos.y))
                song_widget.score.set_offset(Coord2d(item_pos.x+0.75, item_pos.y-0.03))
                song_widget.track_display.set_offset(Coord2d(track_pos.x, track_pos.y))
                song_widget.track_down.set_offset(Coord2d(track_pos.x-0.02, track_pos.y + 0.02))
                song_widget.track_up.set_offset(Coord2d(track_pos.x+0.3, track_pos.y + 0.02))

                song_widget.play.set_disabled(item_pos.y < -1.0 or item_pos.y > cutoff)
                song_widget.delete.set_disabled(item_pos.y < -1.0 or item_pos.y > cutoff)
                song_widget.reload.set_disabled(item_pos.y < -1.0 or item_pos.y > cutoff)
                song_widget.score.set_disabled(item_pos.y < -1.0 or item_pos.y-0.03 > cutoff)
                song_widget.track_display.set_disabled(item_pos.y < -1.0 or track_pos.y > cutoff)
                song_widget.track_down.set_disabled(item_pos.y < -1.0 or track_pos.y + 0.02 > cutoff)
                song_widget.track_up.set_disabled(item_pos.y < -1.0 or track_pos.y + 0.02 > cutoff)
                item_pos.y -= SONG_SPACING
            item_pos.y -= ALBUM_SPACING


    def get_song_score_text(self, song, mode: MusicMode = MusicMode.PERFORMANCE):
        cur_score = 0 if mode not in song.score else song.score[mode]
        return f"{round(cur_score)}/{round(song.get_max_score())} XP"


    def refresh_song_display(self):
        num_albums = self.songbook.get_num_albums()
        for i in range(num_albums):
            album = self.songbook.albums[i]
            album_widget = self.song_albums[i]

            for count, song in enumerate(album.songs):
                song_widget = album_widget.songs[count]
                song_widget.play.set_text(song.get_name(), 12, Coord2d(0.08, -0.02))

                song_widget.score.set_text(self.get_song_score_text(song), 14)
                song_widget.track_display.set_text(get_track_display_text(song), 9)
        self._set_album_menu_pos()


    def prepare(self, font, music, songbook):
        self.font = font
        self.music = music
        self.songbook = songbook

        menu_thirds = 2.0 / 4

        # Bar to highlight the menu options at top of screen
        self.menus[Menus.SONGS].add_create_widget(self.textures.create("vgradient.png", Coord2d(0.0, MenuConfig.MENU_ROW_Y), Coord2d(2.0, 0.5), [0.7, 0.5, 0.7, 0.56]))

        # Scroll indicator for song list
        self.menus[Menus.SONGS].add_create_widget(self.textures.create(None, Coord2d(SONG_SCRL_PX, SONG_SCRL_PY),  Coord2d(SONG_SCRL_SX, SONG_SCRL_SY), [0.4, 0.4, 0.4, 0.5]))
        self.scroll_widget = self.menus[Menus.SONGS].add_create_widget(self.textures.create("gui/sliderknob.png", Coord2d(SONG_SCRL_PX, SONG_SCRL_PY + SONG_SCRL_H * 0.5), Coord2d(0.035, 0.035 * self.window_ratio)))

        # Scroll buttons
        WidgetFactory.create_button_pair(
            self.menus[Menus.SONGS], self.textures, self.window_ratio,
            "gui/btnup.png", "gui/btndown.png",
            Coord2d(SONG_SCRL_PX, SONG_SCRL_PY), SONG_SCRL_SX,
            song_list_scroll, {"menu": self, "dir": -0.333},
            song_list_scroll, {"menu": self, "dir": 0.333},
            width=0.0, height=SONG_SCRL_SY * 0.5
        )
        self.input.add_scroll_mapping(song_list_scroll, {"menu":self})

        # Create album and song widgets
        num_albums = self.songbook.get_num_albums()
        for i in range(num_albums):
            album = self.songbook.albums[i]

            album_name = WidgetFactory.create_text(
                self.menus[Menus.SONGS], self.font,
                album.name, 16, color=MenuConfig.TEXT_COLOR_NORMAL
            )
            album_widget = AlbumWidget(album_name, [])
            self.song_albums.append(album_widget)

            for song in album.songs:
                song_widget = self._create_song_widget(album, song)
                album_widget.songs.append(song_widget)

        self.refresh_song_display()

        # Top menu buttons
        WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btn_devices.png",
            Coord2d(-1.0 + menu_thirds * 1, MenuConfig.MENU_ROW_Y), MenuConfig.MENU_ITEM_SIZE,
            self.show_dialog, {"menu": self, "type": Dialogs.DEVICES}
        )

        self.menus[Menus.SONGS].add_create_widget(
            self.textures.create("gui/btn_options.png", Coord2d(-1.0 + menu_thirds * 2, MenuConfig.MENU_ROW_Y), MenuConfig.MENU_ITEM_SIZE)
        )
        
        WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btn_quit.png",
            Coord2d(-1.0 + menu_thirds * 3, MenuConfig.MENU_ROW_Y), MenuConfig.MENU_ITEM_SIZE,
            menu_quit, {"menu": self}
        )

        # Setup device dialog
        self._setup_device_dialog()

        # Setup game over dialog
        WidgetFactory.create_text(
            self.dialogs[Dialogs.GAME_OVER], self.font,
            "Song Over !", 24, Coord2d(-0.2, 0.2),
            color=MenuConfig.TEXT_COLOR_BRIGHT
        )

        score_widget = WidgetFactory.create_text(
            self.dialogs[Dialogs.GAME_OVER], self.font,
            "Score: 0", 18, Coord2d(-0.175, 0.0),
            color=MenuConfig.TEXT_COLOR_BRIGHT
        )
        score_widget.name = "score"

        retry_widget = WidgetFactory.create_button(
            self.dialogs[Dialogs.GAME_OVER], self.textures, "gui/panel.tga",
            Coord2d(0.2, -0.25), Coord2d(0.2, 0.09 * self.window_ratio),
            font=self.font, text="Retry", text_size=11,
            text_offset=Coord2d(-0.05, -0.015)
        )
        retry_widget.name = "retry"
        retry_widget.set_text_colour(MenuConfig.TEXT_COLOR_DIM)

        back_widget = WidgetFactory.create_button(
            self.dialogs[Dialogs.GAME_OVER], self.textures, "gui/panel.tga",
            Coord2d(-0.15, -0.25), Coord2d(0.27, 0.09 * self.window_ratio),
            font=self.font, text="Play Another", text_size=11,
            text_offset=Coord2d(-0.1, -0.015)
        )
        back_widget.name = "back"
        back_widget.set_text_colour(MenuConfig.TEXT_COLOR_DIM)


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
                scroll_max = 20 * SONG_SPACING
                scrl_frac = self.song_scroll / scroll_max
                scrl_start = SONG_SCRL_PY + (SONG_SCRL_H * 0.5)
                self.scroll_widget.set_offset(Coord2d(SONG_SCRL_PX, scrl_start - (scrl_frac * SONG_SCRL_H)))
                self._set_album_menu_pos()

        devices_active = self.is_dialog_active(Dialogs.DEVICES)
        if devices_active:
            self.devices.update()
            for m in self.devices.get_input_messages():
                m_output = f"{m.type}"
                if hasattr(m, "note"):
                    m_output += f" Note {m.note} - {Notes.note_number_to_name(m.note)}"
                    self.device_note_input_widget.set_text(m_output, 8)
            self.devices.input_flush()


    def set_event(self, name:str):
        """Element specific per-event updates"""
        if name == "score_vfx":
            self.note_correct_colour = [1.0 for index, i in enumerate(self.note_correct_colour) if index <= 3]


    def transition(self, from_menu: Menus, to_menu: Menus):
        self.menus[from_menu].set_active(False, False)
        self.menus[to_menu].set_active(True, True)


    def get_menu(self, type: Menus) -> Gui:
        return self.menus[type]


    def get_dialog(self, type: Dialogs) -> Gui:
        return self.dialogs[type]


    def is_menu_active(self, type: Menus):
        menu_input, menu_draw = self.menus[type].is_active()
        if self.is_any_dialog_active():
            return False, menu_draw
        return menu_input, menu_draw


    def is_any_dialog_active(self):
        return len({k:v for (k,v) in self.dialogs.items() if v.active_input and v.active_draw}) > 0


    def is_dialog_active(self, type: Dialogs):
        return self.dialogs[type].active_input and self.dialogs[type].active_draw


    def show_dialog(self, **kwargs):
        menu = kwargs["menu"]
        type = kwargs["type"]
        if type == Dialogs.DEVICES:
            self.menus[Menus.SONGS].set_active(True, False)
        menu.dialogs[type].set_active(True, True)
        menu.dialog_overlay.set_disabled(False)


    def hide_dialog(self, **kwargs):
        menu = kwargs["menu"]
        type = kwargs["type"]
        if type == Dialogs.DEVICES:
            self.menus[Menus.SONGS].set_active(True, True)
        menu.dialogs[type].set_active(False, False)
        # Hide the overlay if no dialogs are active
        if not menu.is_any_dialog_active():
            menu.dialog_overlay.set_disabled(True)


