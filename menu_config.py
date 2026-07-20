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

    # Career strip sits under the top nav, above the song list
    CAREER_STRIP_Y = 0.52
    CAREER_STRIP_SIZE = Coord2d(1.75, 0.13)
    CAREER_STRIP_COLOR = [0.18, 0.10, 0.24, 0.75]
    CAREER_TITLE_POS = Coord2d(-0.82, CAREER_STRIP_Y)
    CAREER_STATUS_POS = Coord2d(-0.52, CAREER_STRIP_Y)
    CAREER_BUTTON_POS = Coord2d(0.62, CAREER_STRIP_Y)
    # Absolute NDC size so the button fits inside the strip height
    CAREER_BUTTON_SIZE = Coord2d(0.216, 0.085)
    CAREER_BUTTON_TEXT_SIZE = 9
    CAREER_BUTTON_TEXT_OFFSET = Coord2d(-0.07, -0.01)

    # Fixed song-list header (does not scroll with albums)
    SONGS_HEADER_POS = Coord2d(-0.5, 0.38)
    # Hide song rows once they reach the header / career strip
    SONG_LIST_TOP_CUTOFF = 0.34
    SONG_LIST_START_Y = 0.22

    # Song scrollbar: equal vertical margin under career strip and above page bottom
    PAGE_BOTTOM = -1.0
    CAREER_STRIP_BOTTOM = CAREER_STRIP_Y - CAREER_STRIP_SIZE.y * 0.5
    SONG_SCRL_PADDING = 0.06
    SONG_SCRL_PX = 0.9
    SONG_SCRL_SX = 0.05
    SONG_SCRL_SY = (CAREER_STRIP_BOTTOM - PAGE_BOTTOM) - (2.0 * SONG_SCRL_PADDING)
    SONG_SCRL_PY = (CAREER_STRIP_BOTTOM + PAGE_BOTTOM) * 0.5
    SONG_SCRL_H = SONG_SCRL_SY - SONG_SCRL_SX * 3

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
