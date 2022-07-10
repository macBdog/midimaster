from enum import Enum, auto

from gamejam.animation import Animation, AnimType
from gamejam.gui import Gui
from gamejam.input import Input
from gamejam.settings import GameSettings

from song import Song
from staff import Staff
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

    """Utility class to separate all the gui element drawing from main game logic."""
    def __init__(self, graphics, input: Input, gui: Gui, width: int, height: int, textures):
        self.menus = {}
        self.dialogs = {}
        self.elements = {m:{} for m in Menus}
        self.graphics = graphics
        self.input = input
        self.window_width = width
        self.window_height = height
        self.window_ratio = width / height
        self.textures = textures
        self.song_widgets = []
        self.song_scroll = 0.0
        self.note_correct_colour = [0.75, 0.75, 0.75, 0.75]
        self.running = True

        def quit(self):
            self.running = False

        self.input.cursor.set_sprite(self.textures.create_sprite_texture("gui/cursor.png", [0, 0], [0.25, 0.25 * self.window_ratio]))

        # Create sub-guis for each screen of the game, starting with active splash screen
        self.menus[Menus.SPLASH] = Gui(self.window_width, self.window_height, "splash_screen")
        self.menus[Menus.SPLASH].set_active(True, True)
        self.menus[Menus.SPLASH].add_widget(self.textures.create_sprite_texture("splash_background.png", [0, 0], [2.0, 2.0]))
        gui.add_child(self.menus[Menus.SPLASH])

        title = self.menus[Menus.SPLASH].add_widget(self.textures.create_sprite_texture("gui/imgtitle.tga", [0, 0], [0.6, 0.6]))
        title.animation = Animation(AnimType.InOutSmooth, 0.15 if GameSettings.DEV_MODE else 2.0)
        self._set_elem(Menus.SPLASH, "title", title)

        menu_row = 0.8
        menu_thirds = 2.0 / 4
        menu_item_size = [0.31, 0.18]
        self.menus[Menus.SONGS] = Gui(self.window_width, self.window_height, "menu_screen")
        self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/menu_bg.png", [0, 0], [2.0, 2.0]))
        self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btn_devices.png", [-1.0 + menu_thirds * 1, menu_row], menu_item_size))
        self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btn_options.png", [-1.0 + menu_thirds * 2, menu_row], menu_item_size))
        btn_quit = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btn_quit.png", [-1.0 + menu_thirds * 3, menu_row], menu_item_size))
        btn_quit.set_action(quit, self)
        gui.add_child(self.menus[Menus.SONGS])
        
        game_bg_pos_x = Staff.Pos[0] + Staff.Width * 0.5
        self.menus[Menus.GAME] = Gui(self.window_width, self.window_height, "game_screen")
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
            song_pos = [-0.333, self.song_scroll + (0.4 - i * Menu.SONG_SPACING)]
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
            widget = self.song_widgets[song_id]
            widget["track_display"].set_text(get_track_display_text(song), 9, None)

        def song_track_down(song_id: int):
            song = self.songbook.get_song(song_id)
            song.player_track_id = max(song.player_track_id-1, 0)
            widget = self.song_widgets[song_id]
            widget["track_display"].set_text(get_track_display_text(song), 9, None)

        def song_list_scroll(dir: float):
            scroll_max = len(self.song_widgets) * Menu.SONG_SPACING
            self.song_scroll = max(0, min(self.song_scroll + dir, scroll_max))
            self.scroll_widget.set_pos([0.9, 0.73 - (1.44 * (self.song_scroll / scroll_max))])
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
        scroll_up_widget.set_action(song_list_scroll, -0.1)
        scroll_down_widget = self.menus[Menus.SONGS].add_widget(self.textures.create_sprite_texture("gui/btnup.png", [0.9,-0.8], [0.05, -0.05 * self.window_ratio]))
        scroll_down_widget.set_action(song_list_scroll, 0.1)

        num_songs = self.songbook.get_num_songs()
        for i in range(num_songs):
            song = self.songbook.get_song(i)

            play_widget = self.menus[Menus.SONGS].add_widget(
                self.textures.create_sprite_texture("gui/btnplay.tga", [0,0], [0.125, 0.1]), self.font
            )
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
            track_display_widget.set_text_colour([0.7, 0.7, 0.7, 0.7])

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


    def update(self, dt: float, music_running: bool):
        """Element specific per-frame updates"""
        for _, (type, menu) in enumerate(self.elements.items()):
            if self.is_menu_active(type):
                for _, (name, widget) in enumerate(menu.items()):
                    if menu is Menus.GAME:
                        if name == "bg": widget.draw(dt if music_running else dt * 0.1)
                        if name == "note_bg_btm": widget.sprite.set_colour(self.note_correct_colour)
                        if name == "note_bg_top": widget.sprite.set_colour(self.note_correct_colour)

                        self.note_correct_colour = [max(0.65, i - 0.5 * dt) for index, i in enumerate(self.note_correct_colour) if index <= 3]


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
