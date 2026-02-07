import mido

from enum import Enum, auto
from gamejam.coord import Coord2d
from gamejam.quickmaff import clamp
from song import Song
from menu_config import Dialogs

ALBUM_SPACING = 0.33
SONG_SPACING = 0.25
DIALOG_COLOUR = [0.26, 0.15, 0.32, 1.0]
ACTIVE_COLOR = [1.0] * 4
INACTIVE_COLOR = [0.6] * 4

# General MIDI Instrument Map (selected common instruments)
MIDI_INSTRUMENTS = {
    "Acoustic Piano": 0,
    "Electric Piano": 4,
    "Harpsichord": 6,
    "Vibraphone": 11,
    "Marimba": 12,
    "Church Organ": 19,
    "Accordion": 21,
    "Nylon Guitar": 24,
    "Steel Guitar": 25,
    "Jazz Guitar": 26,
    "Acoustic Bass": 32,
    "Fingered Bass": 33,
    "Slap Bass": 36,
    "Violin": 40,
    "Cello": 42,
    "Strings": 48,
    "Choir": 52,
    "Trumpet": 56,
    "Trombone": 57,
    "French Horn": 60,
    "Alto Sax": 65,
    "Tenor Sax": 66,
    "Oboe": 68,
    "Clarinet": 71,
    "Flute": 73,
    "Synth Lead": 80,
    "Synth Pad": 88,
}

# Reverse lookup for displaying current instrument name
MIDI_PROGRAM_TO_NAME = {v: k for k, v in MIDI_INSTRUMENTS.items()}
INSTRUMENT_NAMES = list(MIDI_INSTRUMENTS.keys())

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

class Menus(Enum):
    SPLASH = auto()
    SONGS = auto()
    GAME = auto()

def song_play(**kwargs):
    menu=kwargs["menu"]
    song=kwargs["song"]
    menu.music.load(song)

    # Send program change to set player's instrument
    program_change = mido.Message("program_change", program=menu.songbook.player_instrument)
    menu.devices.output(program_change)

    # Reset trophy animations to animate from full to empty every time we enter game screen
    from score import score_reset_ui
    if menu.game:
        score_reset_ui(menu.game)

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

    # When called from scroll callback, dir is suppled as None
    if "dir" in kwargs:
        dir=kwargs["dir"]
    elif "y" in kwargs:
        dir = kwargs["y"]

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

def get_device_output_disabled(**kwargs) -> bool:
    return not get_device_output_dir(**kwargs)

def devices_refresh(**kwargs):
    menu=kwargs["menu"]
    menu.devices.refresh_io()

def devices_output_test(**kwargs):
    menu = kwargs["menu"]
    # Send program change to set instrument
    import mido
    program_change = mido.Message("program_change", program=menu.songbook.player_instrument)
    menu.devices.output(program_change)
    # Play test note
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

def get_device_input_disabled(**kwargs) -> bool:
    return not get_device_input_dir(**kwargs)

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
    # Send program change to set player's instrument
    import mido
    program_change = mido.Message("program_change", program=game.menu.songbook.player_instrument)
    game.devices.output(program_change)
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

    kwargs.update({"type": Dialogs.GAME_OVER})
    game.menu.hide_dialog(**kwargs)
    game.menu.transition(Menus.GAME, Menus.SONGS)
    game.menu.refresh_song_display()

def game_play_button_colour(**kwargs):
    game = kwargs["game"]
    return [0.1, 0.87, 0.11, 1.0] if game.music_running else [0.8, 0.8, 0.8, 1.0]

def game_pause_button_colour(**kwargs):
    game = kwargs["game"]
    return [0.3, 0.27, 0.81, 1.0] if not game.music_running else [0.8, 0.8, 0.8, 1.0]

def song_over_back(**kwargs):
    menu = kwargs["menu"]
    game = kwargs["game"]
    menu.dialogs[Dialogs.GAME_OVER].set_active(False, False)

    game.reset()
    game.music.rewind()
    game_back_to_menu(**{"menu": menu, "game":game})

def song_over_retry(**kwargs):
    game = kwargs["game"]

    kwargs.update({"type": Dialogs.GAME_OVER})
    game.menu.hide_dialog(**kwargs)
    game.menu.refresh_song_display()
    game.reset()
    game.music.rewind()

def toggle_show_note_names(**kwargs):
    menu = kwargs["menu"]
    menu.songbook.show_note_names = not menu.songbook.show_note_names
    widget_on = kwargs["widget_on"]
    widget_off = kwargs["widget_off"]
    widget_on.set_disabled(not menu.songbook.show_note_names)
    widget_off.set_disabled(menu.songbook.show_note_names)

def toggle_click(**kwargs):
    menu = kwargs["menu"]
    menu.music.click = not  menu.music.click
    widget_on = kwargs["widget_on"]
    widget_off = kwargs["widget_off"]
    widget_on.set_disabled(not menu.music.click)
    widget_off.set_disabled(menu.music.click)

def adjust_output_latency(**kwargs):
    menu = kwargs["menu"]
    direction = kwargs["dir"]
    menu.songbook.output_latency_ms += direction * 10
    widget = kwargs["widget"]
    widget.set_text(f"{menu.songbook.output_latency_ms}ms", 11)

def options_latency_test_start(**kwargs):
    menu = kwargs["menu"]
    import time
    import mido
    # Send program change to set player's instrument
    program_change = mido.Message("program_change", program=menu.songbook.player_instrument)
    menu.devices.output(program_change)

    menu.options_latency_test_running = True
    menu.options_latency_test_cycle_start_time = time.time()
    menu.options_latency_note_played = False
    menu.options_output_anim.reset(time=1.0)
    menu.options_output_anim.active = True
    menu.options_output_anim.loop = True  # Loop the animation
    menu.options_input_anim.reset(time=1.0)
    menu.options_input_anim.active = False
    menu.options_score_widget.set_text("---", 10)

def options_latency_test_stop(**kwargs):
    menu = kwargs["menu"]
    menu.options_latency_test_running = False
    menu.options_latency_test_cycle_start_time = None
    menu.options_latency_note_play_time = None
    menu.options_latency_note_played = False
    menu.options_output_anim.reset(time=1.0)
    menu.options_output_anim.active = False
    menu.options_output_anim.loop = False
    menu.options_input_anim.reset(time=1.0)
    menu.options_input_anim.active = False
    menu.options_score_widget.set_text("---", 10)

def get_instrument_name(program: int) -> str:
    """Get instrument name from MIDI program number."""
    return MIDI_PROGRAM_TO_NAME.get(program, f"Program {program}")

def set_player_instrument(**kwargs):
    """Change the player's MIDI instrument."""
    menu = kwargs["menu"]
    dir = kwargs["dir"]
    current_program = menu.songbook.player_instrument
    if current_program in MIDI_PROGRAM_TO_NAME:
        current_name = MIDI_PROGRAM_TO_NAME[current_program]
        current_idx = INSTRUMENT_NAMES.index(current_name)
    else:
        current_idx = 0

    # Move to next/prev instrument
    new_idx = clamp(current_idx + dir, 0, len(INSTRUMENT_NAMES) - 1)
    new_name = INSTRUMENT_NAMES[new_idx]
    new_program = MIDI_INSTRUMENTS[new_name]
    menu.songbook.player_instrument = new_program

    # Update widget if provided
    if "widget" in kwargs:
        widget = kwargs["widget"]
        widget.set_text(new_name, 9)

    program_change = mido.Message("program_change", program=new_program)
    menu.devices.output(program_change)

def get_player_instrument_disabled(**kwargs) -> bool:
    """Check if instrument navigation buttons should be disabled."""
    menu = kwargs["menu"]
    dir = kwargs["dir"]

    current_program = menu.songbook.player_instrument
    if current_program in MIDI_PROGRAM_TO_NAME:
        current_name = MIDI_PROGRAM_TO_NAME[current_program]
        current_idx = INSTRUMENT_NAMES.index(current_name)
    else:
        current_idx = 0

    new_idx = current_idx + dir
    return new_idx < 0 or new_idx >= len(INSTRUMENT_NAMES)