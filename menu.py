import time

from dataclasses import dataclass
from typing import List

from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.gui import Gui
from gamejam.graphics import Graphics
from gamejam.input import Input
from gamejam.settings import GameSettings
from gamejam.quickmaff import lerp
from gamejam.texture import TextureManager
from gamejam.widget import Widget

from music import Music
from notes import Notes
from song_book import SongBook
from staff import Staff
from midi_devices import MidiDevices
from scrolling_background import ScrollingBackground
from menu_config import MenuConfig, Dialogs
from menu_func import (
    ALBUM_SPACING, SONG_SPACING,
    MusicMode, Menus,
    song_play, song_reload, song_delete, song_track_up, song_track_down, song_list_scroll,
    get_track_display_text,
    menu_quit, menu_transition,
)
from widget_factory import WidgetFactory
from dialog_devices import create_devices_dialog, setup_devices_dialog
from dialog_options import create_options_dialog, setup_options_dialog


@dataclass(init=False)
class SongWidget:
    play: Widget
    score: Widget
    delete: Widget | None
    reload: Widget | None
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
        self.menus: dict[Menus, Gui] = {}
        self.dialogs: dict[Menus, Gui] = {}
        self.elements: dict[Menus, Widget] = {m:{} for m in Menus}
        self.graphics: Graphics = graphics
        self.input: Input = input
        self.devices: MidiDevices = devices
        self.window_width: int = width
        self.window_height: int = height
        self.window_ratio = width / height
        self.textures: TextureManager = textures
        self.song_albums: list[AlbumWidget] = []
        self.song_scroll = 0.0
        self.song_scroll_target = 0.0
        self.running = True
        self.dialog_overlay = None
        self.game = None  # Reference to MidiMaster game object, set after initialization

        # Options dialog latency test state
        self.options_latency_test_running = False
        self.options_latency_test_cycle_start_time = None  # When the current 1-second cycle started
        self.options_latency_note_play_time = None  # When the note should actually play
        self.options_latency_note_played = False  # Whether we've played the note for this cycle

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
        title = self.menus[Menus.SPLASH].add_create_widget(name="splash_title", sprite=self.textures.create_sprite_texture("gui/imgtitle.tga", Coord2d(), Coord2d(0.6, 0.6), wrap=False))
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

        # Add gradients above and below the staff that pulse with correct notes
        note_bg_top = self.menus[Menus.GAME].add_create_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", [0.5] * 4, Coord2d(game_bg_pos_x, Staff.Pos[1] + (Staff.StaffSpacing * 4.0) + (MenuConfig.NOTE_BG_SIZE_TOP * 0.5)), Coord2d(Staff.Width, MenuConfig.NOTE_BG_SIZE_TOP * -1.0))
        )
        note_bg_btm = self.menus[Menus.GAME].add_create_widget(
            self.textures.create_sprite_texture_tinted("vgradient.png", [0.5] * 4, Coord2d(game_bg_pos_x, Staff.Pos[1] - MenuConfig.NOTE_BG_SIZE_BTM * 0.5), Coord2d(Staff.Width, MenuConfig.NOTE_BG_SIZE_BTM))
        )
        self._set_elem(Menus.GAME, "note_bg_top", note_bg_top)
        self._set_elem(Menus.GAME, "note_bg_btm", note_bg_btm)
        self._set_elem(Menus.GAME, "bg", ScrollingBackground(self.graphics, self.textures, "menu_glyphs.tga"))

    def _create_dialogs(self, parent_gui: Gui):
        """Create and configure all dialog windows"""
        # Devices dialog
        self.dialogs[Dialogs.DEVICES] = create_devices_dialog(
            parent_gui, self.graphics, self.textures, self.window_ratio, self.hide_dialog, self
        )

        # Game over dialog
        self.dialogs[Dialogs.GAME_OVER] = Gui("game_over", self.graphics, parent_gui.debug_font, False)
        WidgetFactory.create_dialog_background(self.dialogs[Dialogs.GAME_OVER], self.textures, MenuConfig.GAME_OVER_DIALOG_SIZE)
        parent_gui.add_child(self.dialogs[Dialogs.GAME_OVER])

        # Options dialog
        self.dialogs[Dialogs.OPTIONS] = create_options_dialog(
            parent_gui, self.graphics, self.textures, self.window_ratio, self.hide_dialog, self
        )
    
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
        if song.saved:
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
                if hasattr(song_widget, 'delete'):
                    song_widget.delete.set_offset(Coord2d(item_pos.x-0.09, item_pos.y))
                if hasattr(song_widget, 'reload'):
                    song_widget.reload.set_offset(Coord2d(item_pos.x-0.14, item_pos.y))
                song_widget.score.set_offset(Coord2d(item_pos.x+0.75, item_pos.y-0.03))
                song_widget.track_display.set_offset(Coord2d(track_pos.x, track_pos.y))
                song_widget.track_down.set_offset(Coord2d(track_pos.x-0.02, track_pos.y + 0.02))
                song_widget.track_up.set_offset(Coord2d(track_pos.x+0.3, track_pos.y + 0.02))

                song_widget.play.set_disabled(item_pos.y < -1.0 or item_pos.y > cutoff)
                if hasattr(song_widget, 'delete'):
                    song_widget.delete.set_disabled(item_pos.y < -1.0 or item_pos.y > cutoff)
                if hasattr(song_widget, 'reload'):
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
        self.music: Music = music
        self.songbook: SongBook = songbook

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

        WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btn_options.png",
            Coord2d(-1.0 + menu_thirds * 2, MenuConfig.MENU_ROW_Y), MenuConfig.MENU_ITEM_SIZE,
            self.show_dialog, {"menu": self, "type": Dialogs.OPTIONS}
        )
        
        WidgetFactory.create_button(
            self.menus[Menus.SONGS], self.textures, "gui/btn_quit.png",
            Coord2d(-1.0 + menu_thirds * 3, MenuConfig.MENU_ROW_Y), MenuConfig.MENU_ITEM_SIZE,
            menu_quit, {"menu": self}
        )

        # Setup device dialog widgets
        (self.device_input_widget, self.device_output_widget, self.device_note_input_widget,
         self.devices_apply, self.devices_test) = setup_devices_dialog(
            self.dialogs[Dialogs.DEVICES], self.font, self.textures, self.window_ratio,
            self.devices, self
        )

        # Setup options dialog widgets
        (self.options_checkbox_on, self.options_checkbox_off, self.options_latency_widget,
         self.options_output_note, self.options_output_anim,
         self.options_input_note, self.options_input_anim,
         self.options_score_widget,
         self.options_latency_start_button, self.options_latency_stop_button) = setup_options_dialog(
            self.dialogs[Dialogs.OPTIONS], self.font, self.textures, self.window_ratio,
            self.songbook, self.music, self
        )

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
            note_correct_colour = [0.5, 0.5, 0.5, 0.5 + (self.game.score_fade * 0.5)]
            self.elements[Menus.GAME]["note_bg_top"].sprite.set_colour(note_correct_colour)
            self.elements[Menus.GAME]["note_bg_btm"].sprite.set_colour(note_correct_colour)

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

        # Options dialog latency test
        options_active = self.is_dialog_active(Dialogs.OPTIONS)
        if options_active and self.options_latency_test_running:
            import time
            current_time = time.time()

            if self.options_latency_test_cycle_start_time is not None:
                elapsed = current_time - self.options_latency_test_cycle_start_time

                # Calculate when the note should play relative to the cycle start
                # Visual animation completes at 1.0 second
                # Note plays at: 1.0s + (output_latency_ms / 1000.0)
                # This allows negative latency (note plays before visual completes)
                latency_seconds = self.songbook.output_latency_ms / 1000.0
                note_play_offset = 1.0 + latency_seconds

                # Check if it's time to play the note
                # note_play_offset = 1.0 + (latency_ms / 1000)
                # - Positive latency (e.g., +100ms): note plays at 1.1s (after visual)
                # - Negative latency (e.g., -200ms): note plays at 0.8s (before visual)
                # - Zero latency: note plays at 1.0s (with visual)
                if not self.options_latency_note_played and elapsed >= note_play_offset:
                    self.devices.output_test(note_val_min=60, note_val_max=61, note_off=False)
                    self.options_latency_note_play_time = current_time
                    self.options_latency_note_played = True

                # Reset cycle every 1.0 second for next iteration
                # Use a slightly longer period if latency is very positive to ensure note plays
                cycle_duration = max(1.0, note_play_offset + 0.1)
                if elapsed >= cycle_duration:
                    self.options_latency_test_cycle_start_time = current_time
                    self.options_latency_note_played = False
                    self.options_latency_note_play_time = None

            self.devices.update()
            for m in self.devices.get_input_messages():
                # Check if player hit the test note (Middle C = 60)
                if hasattr(m, "note") and m.note == 60 and m.type == "note_on":
                    # Calculate timing difference (can be early or late)
                    if self.options_latency_note_play_time is not None:
                        # Note has already played - this is a late or on-time press
                        time_diff = current_time - self.options_latency_note_play_time
                        time_diff_ms = time_diff * 1000
                    elif self.options_latency_test_cycle_start_time is not None:
                        # Calculate expected note play time and compare
                        latency_seconds = self.songbook.output_latency_ms / 1000.0
                        expected_note_time = self.options_latency_test_cycle_start_time + 1.0 + latency_seconds
                        time_diff = current_time - expected_note_time
                        time_diff_ms = time_diff * 1000  # Will be negative if early
                    else:
                        # No cycle running - ignore this press
                        continue

                    # Calculate score (100 points for perfect timing, decreasing with time difference)
                    # Use absolute value since we now track both early and late presses
                    # Perfect timing (0-50ms) = 100 points
                    # Good timing (50-100ms) = 75-100 points
                    # Okay timing (100-200ms) = 50-75 points
                    # Poor (>200ms) = 25-50 points
                    abs_time_diff_ms = abs(time_diff_ms)
                    if abs_time_diff_ms <= 50:
                        score = 100
                    elif abs_time_diff_ms <= 100:
                        score = int(75 + (25 * (1.0 - (abs_time_diff_ms - 50) / 50)))
                    elif abs_time_diff_ms <= 200:
                        score = int(50 + (25 * (1.0 - (abs_time_diff_ms - 100) / 100)))
                    else:
                        score = max(25, int(50 - (abs_time_diff_ms - 200) / 10))

                    # Update score display with timing information
                    timing_rounded = round(time_diff_ms / 10) * 10

                    # Format timing string: positive = late, negative = early
                    if timing_rounded > 0:
                        timing_str = f"+{int(timing_rounded)}ms"
                    elif timing_rounded < 0:
                        timing_str = f"{int(timing_rounded)}ms"
                    else:
                        timing_str = "±0ms"

                    self.options_score_widget.set_text(f"{score} pts {timing_str}", 9)

                    # Trigger input note animation
                    self.options_input_anim.reset(time=1.0)
                    self.options_input_anim.active = True
                    self.options_input_anim.loop = True
            self.devices.input_flush()

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
        if type == Dialogs.OPTIONS:
            self.menus[Menus.SONGS].set_active(True, False)
        if type == Dialogs.GAME_OVER:
            self.elements[Menus.GAME]["note_bg_top"].set_disabled(True)
            self.elements[Menus.GAME]["note_bg_btm"].set_disabled(True)
        menu.dialogs[type].set_active(True, True)
        menu.dialog_overlay.set_disabled(False)

    def hide_dialog(self, **kwargs):
        menu = kwargs["menu"]
        type = kwargs["type"]
        if type == Dialogs.DEVICES:
            self.menus[Menus.SONGS].set_active(True, True)
        if type == Dialogs.OPTIONS:
            self.menus[Menus.SONGS].set_active(True, True)
            menu.options_latency_test_running = False
        if type == Dialogs.GAME_OVER:
            self.elements[Menus.GAME]["note_bg_top"].set_disabled(False)
            self.elements[Menus.GAME]["note_bg_btm"].set_disabled(False)
        menu.dialogs[type].set_active(False, False)
        # Hide the overlay if no dialogs are active
        if not menu.is_any_dialog_active():
            menu.dialog_overlay.set_disabled(True)
        menu.refresh_song_display()


