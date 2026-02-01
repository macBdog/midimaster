"""Widget factory for creating GUI widgets with less boilerplate"""
from typing import Tuple
from gamejam.coord import Coord2d
from gamejam.gui import Gui
from gamejam.texture import TextureManager
from gamejam.font import Font
from gamejam.widget import Widget
from menu_func import DIALOG_COLOUR


class WidgetFactory:
    """Helper class for creating GUI widgets with less boilerplate"""

    @staticmethod
    def create_button(gui: Gui, textures: TextureManager, texture_path: str,
                      pos: Coord2d, size: Coord2d, action=None, action_args: dict=None,
                      font: Font = None, text: str = None, text_size: int = 11,
                      text_offset: Coord2d = None, color_func=None, color_func_args: dict=None,
                      disabled_func=None, disabled_func_args: dict=None) -> Widget:
        """Create a button widget with texture, action, and optional text"""
        widget = gui.add_create_widget(textures.create(texture_path, pos, size), font)

        if disabled_func:
            widget.set_disabled_func(disabled_func, disabled_func_args)

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
                          disabled_func_prev=None, disabled_func_next=None) -> Tuple[Widget, Widget]:
        """Create a pair of navigation buttons (prev/next, up/down, etc.)"""
        button_size = Coord2d(size, size * window_ratio)
        pos_prev = Coord2d(base_pos.x - width, base_pos.y + height)
        widget_prev = WidgetFactory.create_button(
            gui, textures, texture_prev, pos_prev, button_size,
            action_prev, action_args_prev,
            disabled_func=disabled_func_prev, disabled_func_args=action_args_prev
        )

        pos_next = Coord2d(base_pos.x + width, base_pos.y - height)
        widget_next = WidgetFactory.create_button(
            gui, textures, texture_next, pos_next, button_size,
            action_next, action_args_next,
            disabled_func=disabled_func_next, disabled_func_args=action_args_next
        )
        return widget_prev, widget_next

    @staticmethod
    def create_checkbox_pair(gui: Gui, textures: TextureManager, window_ratio: float,
                          texture_on: str, texture_off: str,
                          base_pos: Coord2d, size: float,
                          action, action_args: dict,
                          state: bool = False) -> Tuple[Widget, Widget]:
        """Create a pair of checkbox buttons where the state is inverted between them"""
        button_size = Coord2d(size, size * window_ratio)
        widget_on = WidgetFactory.create_button(
            gui, textures, texture_on, base_pos, button_size,
            action, action_args,
        )

        widget_off = WidgetFactory.create_button(
           gui, textures, texture_off, base_pos, button_size,
           action, action_args,
        )

        action_args.update({"widget_on": widget_on, "widget_off": widget_off})
        widget_on.set_disabled(not state)
        widget_off.set_disabled(state)
        return widget_on, widget_off

    @staticmethod
    def create_dialog_background(gui: Gui, textures: TextureManager,
                                 size: Coord2d, color: list = None) -> Widget:
        """Create a dialog background widget"""
        bg_color = color or DIALOG_COLOUR
        return gui.add_create_widget(textures.create(None, Coord2d(), size, bg_color))
