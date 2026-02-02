"""Options dialog creation and management"""
from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.gui import Gui
from gamejam.texture import TextureManager
from gamejam.font import Font

from menu_config import MenuConfig, Dialogs
from widget_factory import WidgetFactory
from menu_func import (
    toggle_show_note_names, toggle_click,
    adjust_output_latency,
    options_latency_test_start, options_latency_test_stop
)


def create_options_dialog(parent_gui: Gui, graphics, textures: TextureManager, window_ratio: float, hide_dialog_func, menu) -> Gui:
    """Create the options dialog"""
    dialog = Gui("options", graphics, parent_gui.debug_font, False)
    WidgetFactory.create_dialog_background(dialog, textures, MenuConfig.DEVICE_DIALOG_SIZE)

    # Close button
    close_button_size = Coord2d(MenuConfig.MEDIUM_BUTTON_SIZE, MenuConfig.MEDIUM_BUTTON_SIZE * window_ratio)
    close_button_pos_options = Coord2d(MenuConfig.DEVICE_DIALOG_SIZE.x * 0.5, MenuConfig.DEVICE_DIALOG_SIZE.y * 0.5)
    WidgetFactory.create_button(
        dialog, textures, "gui/checkboxon.tga",
        close_button_pos_options, close_button_size,
        hide_dialog_func, {"menu": menu, "type": Dialogs.OPTIONS}
    )

    parent_gui.add_child(dialog)
    return dialog


def setup_options_dialog(dialog: Gui, font: Font, textures: TextureManager, window_ratio: float,
                        songbook, music, menu):
    """Setup all widgets for the options dialog"""
    options_y = 0.3

    # Show note names option
    WidgetFactory.create_text(
        dialog, font,
        "Show note names", 10, Coord2d(-0.3, options_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )
    options_checkbox_on, options_checkbox_off = WidgetFactory.create_checkbox_pair(
        dialog, textures, window_ratio, "gui/checkboxon.tga", "gui/checkbox.tga",
        Coord2d(0.165, options_y), MenuConfig.SMALL_BUTTON_SIZE,
        toggle_show_note_names, {"menu": menu, "widget": None},
        state=songbook.show_note_names,
    )
    options_y -= 0.1

    # Click track option
    WidgetFactory.create_text(
        dialog, font,
        "Click track", 10, Coord2d(-0.3, options_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )
    options_checkbox_on, options_checkbox_off = WidgetFactory.create_checkbox_pair(
        dialog, textures, window_ratio, "gui/checkboxon.tga", "gui/checkbox.tga",
        Coord2d(0.165, options_y), MenuConfig.SMALL_BUTTON_SIZE,
        toggle_click, {"menu": menu, "widget": None},
        state=music.click,
    )
    options_y -= 0.25

    # Output latency options and tester
    WidgetFactory.create_text(
        dialog, font,
        "Output latency", 10, Coord2d(-0.3, options_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )
    options_latency_widget = WidgetFactory.create_text(
        dialog, font,
        f"{songbook.output_latency_ms}ms", 11, Coord2d(0.0, options_y),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )
    options_y -= 0.015

    WidgetFactory.create_button_pair(
        dialog, textures, window_ratio,
        "gui/btnback.png", "gui/btnnext.png",
        Coord2d(0.2, options_y), MenuConfig.SMALL_BUTTON_SIZE,
        adjust_output_latency, {"menu": menu, "dir": -1, "widget": options_latency_widget},
        adjust_output_latency, {"menu": menu, "dir": 1, "widget": options_latency_widget},
        width=0.06, height=0.0
    )
    options_y -= 0.1

    # Output note widget (what the game plays)
    WidgetFactory.create_text(
        dialog, font,
        "Output Note", 9, Coord2d(-0.15, options_y),
        color=MenuConfig.TEXT_COLOR_DIM
    )
    trophy_size = 0.1
    options_output_note = dialog.add_create_widget(
        textures.create_sprite_texture("trophy2.png", Coord2d(-0.15, options_y - 0.09), Coord2d(trophy_size, trophy_size * window_ratio), wrap=False)
    )
    options_output_anim = options_output_note.animate(AnimType.FillRadial)
    options_output_anim.reset(time=1.0)
    options_output_anim.active = False
    # Note: Timing is handled directly in menu.py update loop, not via animation callback

    # Input note widget (what the player plays)
    WidgetFactory.create_text(
        dialog, font,
        "Input Note", 9, Coord2d(0.15, options_y),
        color=MenuConfig.TEXT_COLOR_DIM
    )
    options_input_note = dialog.add_create_widget(
        textures.create_sprite_texture("trophy1.png", Coord2d(0.15, options_y - 0.09), Coord2d(trophy_size, trophy_size * window_ratio), wrap=False)
    )
    options_input_anim = options_input_note.animate(AnimType.FillRadial)
    options_input_anim.reset(time=1.0)
    options_input_anim.active = False

    # Score display (shows timing accuracy in real-time)
    options_score_widget = WidgetFactory.create_text(
        dialog, font,
        "Score", 10, Coord2d(0.25, options_y - 0.09),
        color=MenuConfig.TEXT_COLOR_BRIGHT
    )

    options_y -= 0.25

    # Test start and stop buttons
    button_size = Coord2d(0.15, 0.06 * window_ratio)
    options_latency_start_button = WidgetFactory.create_button(
        dialog, textures, "gui/panel.tga",
        Coord2d(-0.1, options_y), button_size,
        options_latency_test_start, {"menu": menu},
        font=font, text="Test", text_size=10,
        text_offset=Coord2d(-0.03, -0.012)
    )
    options_latency_start_button.set_text_colour(MenuConfig.TEXT_COLOR_BRIGHT)

    options_latency_stop_button = WidgetFactory.create_button(
        dialog, textures, "gui/panel.tga",
        Coord2d(0.1, options_y), button_size,
        options_latency_test_stop, {"menu": menu},
        font=font, text="Stop", text_size=10,
        text_offset=Coord2d(-0.03, -0.012)
    )
    options_latency_stop_button.set_text_colour(MenuConfig.TEXT_COLOR_BRIGHT)

    return (options_checkbox_on, options_checkbox_off, options_latency_widget,
            options_output_note, options_output_anim,
            options_input_note, options_input_anim,
            options_score_widget,
            options_latency_start_button, options_latency_stop_button)
