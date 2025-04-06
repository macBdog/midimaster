from enum import Enum, auto
from gamejam.coord import Coord2d
from gamejam.quickmaff import clamp
from song import Song


ALBUM_SPACING = 0.33
SONG_SPACING = 0.25
DIALOG_COLOUR = [0.26, 0.15, 0.32, 1.0]
ACTIVE_COLOR = [1.0] * 4
INACTIVE_COLOR = [0.6] * 4

class KeyboardMapping(Enum):
    NOTE_NAMES = auto()
    QWERTY_PIANO = auto()


class MusicMode(Enum):
    PAUSE_AND_LEARN = auto() # Music pauses at each note and counts down from max to min score
    PERFORMANCE = auto() # Each note's score is determined time to note start


class Tropy(Enum):
    VINYL = 0,
    TAPE = 1,
    LASER = 2,


TROPHY_SCORE = [
    0.55,
    0.7,
    0.9,
]


class Menus(Enum):
    SPLASH = auto()
    SONGS = auto()
    GAME = auto()


class Dialogs(Enum):
    DEVICES = auto()
    GAME_OVER = auto()


def song_play(**kwargs):
    menu=kwargs["menu"]
    song=kwargs["song"]
    menu.music.load(song)
    menu.transition(Menus.SONGS, Menus.GAME)


def song_reload(**kwargs):
    menu=kwargs["menu"]
    album=kwargs["album"]
    song=kwargs["song"]
    new_song = Song()
    new_song.from_midi_file(song.path, song.player_track_id)
    album.add_update_song(new_song)
    menu.music.load(new_song)
    menu._set_album_menu_pos()


def song_delete(**kwargs):
    menu=kwargs["menu"]
    album=kwargs["album"]
    song=kwargs["song"]
    widget=kwargs["widget"]
    menu.menus[Menus.SONGS].delete_widget(widget.play)
    menu.menus[Menus.SONGS].delete_widget(widget.score)
    menu.menus[Menus.SONGS].delete_widget(widget.delete)
    menu.menus[Menus.SONGS].delete_widget(widget.reload)
    menu.menus[Menus.SONGS].delete_widget(widget.track_display)
    menu.menus[Menus.SONGS].delete_widget(widget.track_down)
    menu.menus[Menus.SONGS].delete_widget(widget.track_up)
    album.delete_song(song)
    menu._set_album_menu_pos()


def song_track_up(**kwargs):
    widget=kwargs["widget"]
    song=kwargs["song"]
    song.player_track_id += 1
    song.dirty = True
    widget.set_text(get_track_display_text(song), 9)


def song_track_down(**kwargs):
    widget=kwargs["widget"]
    song=kwargs["song"]
    song.player_track_id = max(song.player_track_id-1, 0)
    song.dirty = True
    widget.set_text(get_track_display_text(song), 9)


def song_list_scroll(**kwargs):
    menu=kwargs["menu"]
    _=kwargs["x"]
    y=kwargs["y"]

    # When called from scroll callback, dir is suppled as None
    dir = -0.1 * y 
    if dir in kwargs:
        dir=kwargs["dir"]

    scroll_max = 20 * SONG_SPACING
    menu.song_scroll_target = clamp(menu.song_scroll_target + dir, 0, scroll_max)


def get_track_display_text(song: Song) -> str:
    track = song.player_track_id
    if track in song.track_names:
        return f"{song.player_track_id}: ({song.track_names[song.player_track_id]})"
    else:
        return f"Track {song.player_track_id} (Unknown)"


def set_devices_input(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    if menu.devices.input_device_name in devices:
        cur_device_id = devices.index(menu.devices.input_device_name)
    else:
        cur_device_id = 0
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.input_device_name = devices[cur_device_id]
    menu.device_input_widget.set_text(menu.devices.input_device_name, 10, Coord2d(-0.05, 0.3))
    menu.songbook.input_device = menu.devices.input_device_name


def get_device_input_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    if menu.devices.input_device_name in devices:
        cur_device_id = devices.index(menu.devices.input_device_name)
    else:
        cur_device_id = 0
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_input_col(**kwargs) -> list:
    dir=kwargs["dir"]
    return ACTIVE_COLOR if get_device_input_dir({"dir":dir}) else INACTIVE_COLOR


def set_devices_output(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    cur_device_id = devices.index(menu.devices.output_device_name)
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.output_device_name = devices[cur_device_id]
    menu.device_output_widget.set_text(menu.devices.output_device_name, 10, Coord2d(-0.05, 0.2))
    menu.songbook.output_device = menu.devices.output_device_name


def get_device_output_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    if menu.devices.output_device_name in devices:
        cur_device_id = devices.index(menu.devices.output_device_name)
    else:
        cur_device_id = 0
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_output_col(**kwargs) -> list:
    dir=kwargs["dir"]
    return ACTIVE_COLOR if get_device_output_dir(**kwargs) else INACTIVE_COLOR


def devices_refresh(**kwargs):
    menu=kwargs["menu"]
    menu.devices.refresh_io()


def devices_output_test(**kwargs):
    menu=kwargs["menu"]
    menu.devices.output_test()


def set_devices_input(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    if menu.devices.input_device_name in devices:
        cur_device_id = devices.index(menu.devices.input_device_name)
        cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    else:
        cur_device_id = 0
    menu.devices.input_device_name = devices[cur_device_id]
    menu.device_input_widget.set_text(menu.devices.input_device_name, 10)
    menu.songbook.input_device = menu.devices.input_device_name


def get_device_input_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    cur_device_id = 0 
    if menu.devices.input_device_name in devices:
        cur_device_id = devices.index(menu.devices.input_device_name)
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_input_col(**kwargs) -> list:
    return ACTIVE_COLOR if get_device_input_dir(**kwargs) else INACTIVE_COLOR


def set_devices_output(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    cur_device_id = devices.index(menu.devices.output_device_name)
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.output_device_name = devices[cur_device_id]
    menu.device_output_widget.set_text(menu.devices.output_device_name, 10)
    menu.songbook.output_device = menu.devices.output_device_name


def menu_quit(**kwargs):
    menu = kwargs["menu"]
    menu.songbook.save(menu.songbook)
    menu.running = False


def menu_transition(**kwargs):
    menu = kwargs["menu"]
    t_from = kwargs["from"]
    t_to = kwargs["to"]
    menu.transition(t_from, t_to)


def game_play(**kwargs):
    game = kwargs["game"]
    game.music_running = True


def game_pause(**kwargs):
    game = kwargs["game"]
    game.music_running = False


def game_stop_rewind(**kwargs):
    game = kwargs["game"]
    game.reset()
    game.music.rewind()


def game_mode_toggle(**kwargs):
    game = kwargs["game"]
    game.mode = MusicMode.PAUSE_AND_LEARN if game.mode == MusicMode.PERFORMANCE else MusicMode.PERFORMANCE


def game_back_to_menu(**kwargs):
    game = kwargs["game"]
    menu = kwargs["menu"]
    if menu.dialogs[Dialogs.GAME_OVER].active_input and menu.dialogs[Dialogs.GAME_OVER].active_draw:
        return

    game_pause(**kwargs)
    existing_score = game.music.song.score[game.mode] if game.mode in game.music.song.score else 0
    game.music.song.score[game.mode] = max(game.score, existing_score)
    game.reset()
    game.music.reset()
    game.menu.transition(Menus.GAME, Menus.SONGS)
    game.menu.refresh_song_display()


def game_play_button_colour(**kwargs):
    game = kwargs["game"]
    return [0.1, 0.87, 0.11, 1.0] if game.music_running else [0.8, 0.8, 0.8, 1.0]


def game_pause_button_colour(**kwargs):
    game = kwargs["game"]
    return [0.3, 0.27, 0.81, 1.0] if not game.music_running else [0.8, 0.8, 0.8, 1.0]


def game_score_bg_colour(**kwargs):
    game = kwargs["game"]
    return [1.0, 1.0, 1.0, max(game.score_fade, 0.75)]


def song_over_back(**kwargs):
    menu = kwargs["menu"]
    game = kwargs["game"]
    menu.dialogs[Dialogs.GAME_OVER].set_active(False, False)

    game.reset()
    game.music.rewind()
    game_back_to_menu(**{"menu": menu, "game":game})


def song_over_retry(**kwargs):
    menu = kwargs["menu"]
    game = kwargs["game"]
    menu.dialogs[Dialogs.GAME_OVER].set_active(False, False)

    game.reset()
    game.music.rewind()
