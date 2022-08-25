import time
from enum import Enum, auto
from typing import Any

from gamejam.animation import Animation, AnimType
from gamejam.gui import Gui
from gamejam.input import Input
from gamejam.settings import GameSettings
from gamejam.quickmaff import lerp, clamp

from song import Song
from staff import Staff
from midi_devices import MidiDevices


class Menus(Enum):
    SPLASH = auto()
    SONGS = auto()
    GAME = auto()


class Dialogs(Enum):
    DEVICES = auto()
    GAME_OVER = auto()


def song_play(**kwargs):
    menu=kwargs["menu"]
    song_id=kwargs["song_id"]
    menu.music.load(menu.songbook.get_song(song_id))
    menu.transition(Menus.SONGS, Menus.GAME)


def song_reload(**kwargs):
    menu=kwargs["menu"]
    song_id=kwargs["song_id"]
    existing_song = menu.songbook.get_song(song_id)
    new_song = Song()
    new_song.from_midi_file(existing_song.path, existing_song.player_track_id)
    menu.songbook.add_update_song(new_song)
    menu._set_song_menu_pos()


def song_delete(**kwargs):
    menu=kwargs["menu"]
    song_id=kwargs["song_id"]
    widgets = menu.song_widgets[song_id]
    for elem in widgets:
        menu.menus[Menus.SONGS].delete_widget(widgets[elem])
    menu.song_widgets.pop(song_id)
    menu.songbook.delete_song(song_id)
    menu._set_song_menu_pos()


def song_track_up(**kwargs):
    menu=kwargs["menu"]
    song_id=kwargs["song_id"]
    song = menu.songbook.get_song(song_id)
    song.player_track_id += 1
    song.dirty = True
    widget = menu.song_widgets[song_id]
    widget["track_display"].set_text(get_track_display_text(song), 9, None)


def song_track_down(**kwargs):
    menu=kwargs["menu"]
    song_id=kwargs["song_id"]
    song = menu.songbook.get_song(song_id)
    song.player_track_id = max(song.player_track_id-1, 0)
    song.dirty = True
    widget = menu.song_widgets[song_id]
    widget["track_display"].set_text(get_track_display_text(song), 9, None)


def song_list_scroll(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    xpos=kwargs["xpos"]
    ypos=kwargs["ypos"]

    # When called from scroll callback, dir is suppled as None
    if dir is None:
        dir = -0.1 * ypos  
    scroll_max = len(menu.song_widgets) * Menu.SONG_SPACING
    menu.song_scroll_target = clamp(menu.song_scroll_target + dir, 0, scroll_max)
    menu._set_song_menu_pos()


def get_track_display_text(song) -> str:
    track = song.player_track_id
    if track in song.track_names:
        return f"{song.player_track_id}: ({song.track_names[song.player_track_id]})"
    else:
        return f"Track {song.player_track_id} (Unknown)"


def set_devices_input(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    cur_device_id = devices.index(menu.devices.input_device_name)
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.input_device_name = devices[cur_device_id]
    menu.device_input_widget.set_text(menu.devices.input_device_name, 10, [-0.05,0.3])
    menu.songbook.input_device = menu.devices.input_device_name


def get_device_input_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    cur_device_id = devices.index(menu.devices.input_device_name)
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_input_col(**kwargs) -> list:
    dir=kwargs["dir"]
    return [1.0] * 4 if get_device_input_dir(dir) else [0.4] * 4


def set_devices_output(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    cur_device_id = devices.index(menu.devices.output_device_name)
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.output_device_name = devices[cur_device_id]
    menu.device_output_widget.set_text(menu.devices.output_device_name, 10, [-0.05,0.2])
    menu.songbook.output_device = menu.devices.output_device_name


def get_device_output_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    cur_device_id = devices.index(menu.devices.output_device_name)
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_output_col(**kwargs) -> list:
    dir=kwargs["dir"]
    return [1.0] * 4 if get_device_output_dir(dir) else [0.4] * 4


def devices_refresh(**kwargs):
    menu=kwargs["menu"]
    sleep_delay_ms=kwargs["sleep_delay_ms"]
    menu.devices.refresh_io()


def devices_output_test(**kwargs):
    menu=kwargs["menu"]
    menu.devices.output_test()


def set_devices_input(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    cur_device_id = devices.index(menu.devices.input_device_name)
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.input_device_name = devices[cur_device_id]
    menu.device_input_widget.set_text(menu.devices.input_device_name, 10, [-0.05,0.3])
    menu.songbook.input_device = menu.devices.input_device_name


def get_device_input_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.input_devices
    cur_device_id = devices.index(menu.devices.input_device_name)
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_input_col(**kwargs) -> list:
    return [1.0] * 4 if get_device_input_dir(dir) else [0.4] * 4


def set_devices_output(**kwargs):
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    cur_device_id = devices.index(menu.devices.output_device_name)
    cur_device_id = clamp(cur_device_id + dir, 0, len(devices) - 1)
    menu.devices.output_device_name = devices[cur_device_id]
    menu.device_output_widget.set_text(menu.devices.output_device_name, 10, [-0.05,0.2])
    menu.songbook.output_device = menu.devices.output_device_name


def get_device_output_dir(**kwargs) -> bool:
    menu=kwargs["menu"]
    dir=kwargs["dir"]
    devices = menu.devices.output_devices
    cur_device_id = devices.index(menu.devices.output_device_name)
    return cur_device_id + dir >= 0 and cur_device_id + dir < len(devices)


def get_device_output_col(**kwargs) -> list:
    dir=kwargs["dir"]
    return [1.0] * 4 if get_device_output_dir(dir) else [0.4] * 4


def devices_refresh(**kwargs):
    menu=kwargs["menu"]
    sleep_delay_ms=kwargs["sleep_delay_ms"]
    menu.devices.refresh_io()


def devices_output_test(**kwargs):
    menu=kwargs["menu"]
    menu.devices.output_test()