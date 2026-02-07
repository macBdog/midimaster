"""Devices dialog creation and management"""
from gamejam.coord import Coord2d
from gamejam.gui import Gui
from gamejam.texture import TextureManager
from gamejam.font import Font

from menu_config import MenuConfig, Dialogs
from widget_factory import WidgetFactory
from menu_func import (
    set_devices_input, set_devices_output,
    get_device_input_disabled, get_device_output_disabled,
    devices_refresh, devices_output_test,
    set_player_instrument, get_player_instrument_disabled,
    get_instrument_name
)


def create_devices_dialog(parent_gui: Gui, graphics, textures: TextureManager, window_ratio: float, hide_dialog_func, menu) -> Gui:
    """Create the devices configuration dialog"""
    dialog = Gui("devices", graphics, parent_gui.debug_font, False)
    WidgetFactory.create_dialog_background(dialog, textures, MenuConfig.DEVICE_DIALOG_SIZE)

    # Close button
    close_button_size = Coord2d(MenuConfig.MEDIUM_BUTTON_SIZE, MenuConfig.MEDIUM_BUTTON_SIZE * window_ratio)
    close_button_pos = Coord2d(MenuConfig.DEVICE_DIALOG_SIZE.x * 0.5, MenuConfig.DEVICE_DIALOG_SIZE.y * 0.5)
    WidgetFactory.create_button(
        dialog, textures, "gui/checkboxon.tga",
        close_button_pos, close_button_size,
        hide_dialog_func, {"menu": menu, "type": Dialogs.DEVICES}
    )

    parent_gui.add_child(dialog)
    return dialog


def setup_devices_dialog(dialog: Gui, font: Font, textures: TextureManager, window_ratio: float,
                        devices, menu):
    """Setup all widgets for the device configuration dialog"""
    # Input device section
    dialog_y = 0.25
    WidgetFactory.create_text(
        dialog, font,
        "Input ", 8, Coord2d(-0.3, dialog_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )

    device_input_widget = WidgetFactory.create_text(
        dialog, font,
        devices.input_device_name, 8, Coord2d(-0.05, dialog_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )

    WidgetFactory.create_button_pair(
        dialog, textures, window_ratio,
        "gui/btnback.png", "gui/btnnext.png",
        Coord2d(0.12, dialog_y + 0.015), MenuConfig.SMALL_BUTTON_SIZE,
        set_devices_input, {"menu": menu, "dir": -1},
        set_devices_input, {"menu": menu, "dir": 1},
        width=0.2, height=0.0,
        disabled_func_prev=get_device_input_disabled,
        disabled_func_next=get_device_input_disabled
    )
    dialog_y -= MenuConfig.DIALOG_LINE_HEIGHT

    # Output device section
    WidgetFactory.create_text(
        dialog, font,
        "Output: ", 8, Coord2d(-0.3, dialog_y),
        color=MenuConfig.TEXT_COLOR_DIM
    )
    device_output_widget = WidgetFactory.create_text(
        dialog, font,
        devices.output_device_name, 8, Coord2d(-0.05, dialog_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )

    WidgetFactory.create_button_pair(
        dialog, textures, window_ratio,
        "gui/btnback.png", "gui/btnnext.png",
        Coord2d(0.12, dialog_y + MenuConfig.BUTTON_PAIR_OFFSET_Y), MenuConfig.SMALL_BUTTON_SIZE,
        set_devices_output, {"menu": menu, "dir": -1},
        set_devices_output, {"menu": menu, "dir": 1},
        width=0.2, height=0.0,
        disabled_func_prev=get_device_output_disabled,
        disabled_func_next=get_device_output_disabled
    )
    dialog_y -= MenuConfig.DIALOG_LINE_HEIGHT

    # Player instrument section
    WidgetFactory.create_text(
        dialog, font,
        "Instrument: ", 8, Coord2d(-0.3, dialog_y),
        color=MenuConfig.TEXT_COLOR_DIM
    )
    instrument_name = get_instrument_name(menu.songbook.player_instrument)
    device_instrument_widget = WidgetFactory.create_text(
        dialog, font,
        instrument_name, 9, Coord2d(-0.05, dialog_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )
    WidgetFactory.create_button_pair(
        dialog, textures, window_ratio,
        "gui/btnback.png", "gui/btnnext.png",
        Coord2d(0.12, dialog_y + MenuConfig.BUTTON_PAIR_OFFSET_Y), MenuConfig.SMALL_BUTTON_SIZE,
        set_player_instrument, {"menu": menu, "dir": -1, "widget": device_instrument_widget},
        set_player_instrument, {"menu": menu, "dir": 1, "widget": device_instrument_widget},
        width=0.2, height=0.0,
        disabled_func_prev=get_player_instrument_disabled,
        disabled_func_next=get_player_instrument_disabled
    )
    dialog_y -= MenuConfig.DIALOG_LINE_HEIGHT

    # Note input display
    WidgetFactory.create_text(
        dialog, font,
        "Note Input: ", 10, Coord2d(-0.3, dialog_y),
        color=MenuConfig.TEXT_COLOR_DIM
    )
    device_note_input_widget = WidgetFactory.create_text(
        dialog, font,
        "N/A", 8, Coord2d(-0.05, dialog_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )

    # Action buttons
    devices_apply = WidgetFactory.create_button(
        dialog, textures, "gui/panel.tga",
        Coord2d(0.2, -0.2), Coord2d(0.2, 0.08 * window_ratio),
        devices_refresh, {"menu": menu},
        font=font, text="Reconnect", text_size=11,
        text_offset=Coord2d(-0.07, -0.015)
    )
    devices_apply.set_text_colour(MenuConfig.TEXT_COLOR_BRIGHT)

    devices_test = WidgetFactory.create_button(
        dialog, textures, "gui/panel.tga",
        Coord2d(-0.2, -0.2), Coord2d(0.25, 0.08 * window_ratio),
        devices_output_test, {"menu": menu},
        font=font, text="Test Output", text_size=11,
        text_offset=Coord2d(-0.1, -0.015)
    )
    devices_test.set_text_colour(MenuConfig.TEXT_COLOR_BRIGHT)

    return (device_input_widget, device_output_widget, device_instrument_widget,
            device_note_input_widget, devices_apply, devices_test)
