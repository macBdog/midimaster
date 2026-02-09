"""Menu configuration constants and enums"""
from enum import Enum, auto
from gamejam.coord import Coord2d


class Dialogs(Enum):
    DEVICES = auto()
    GAME_OVER = auto()
    OPTIONS = auto()

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
    NOTE_BG_SIZE_TOP = 0.35
    NOTE_BG_SIZE_BTM = 0.85

    # General GUI spacing
    DIALOG_LINE_HEIGHT = 0.1
    BUTTON_PAIR_OFFSET_Y = 0.015

    # Device dialog
    DEVICE_DIALOG_SIZE = Coord2d(0.8, 1.0)
    DEVICE_BUTTON_SPACING = 0.4  # Horizontal spacing between left and right buttons

    # Options dialog
    OPTIONS_DIALOG_SIZE = Coord2d(0.8, 1.2)

    # Game over dialog
    GAME_OVER_DIALOG_SIZE = Coord2d(0.7, 0.9)
