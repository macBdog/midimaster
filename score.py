import math
from gamejam.animation import Animation, AnimType
from gamejam.coord import Coord2d
from gamejam.widget import Alignment, AlignX, AlignY

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from midimaster import MidiMaster
    from gamejam.gui import Gui


TROPHY_SCORE = [
    0.55,  # Gold trophy (easiest) - 55% of max score
    0.80,  # Platinum trophy (middle) - 80% of max score
    0.95,  # Diamond trophy (hardest) - 95% of max score
]

MAX_SCORE_PER_NOTE = 10.0
REQUIRED_HOLD_FRACTION = 0.75

def reset_trophy(**kwargs):
    trophy: Animation = kwargs["trophy"]
    trophy.frac = 0
    trophy.active = False

def score_reset_ui(game: 'MidiMaster'):
    """Reset all score UI elements for a new song."""
    for i in range(3):
        if hasattr(game, 'trophy') and len(game.trophy) > i:
            trophy_anim: Animation = game.trophy[i].animation
            trophy_anim.reset(time=0.5)
            trophy_anim.active = True
            trophy_anim.loop = False
            trophy_anim.set_animation(AnimType.FillRadial, True)
            trophy_anim.set_action(1.0, reset_trophy, {"trophy": trophy_anim})

    # Reset score bar to empty
    if hasattr(game, 'score_bar') and game.score_bar:
        score_bar_anim = game.score_bar.animation
        score_bar_anim.frac = 0.0
        score_bar_anim.active = False
        score_bar_anim.set_animation(AnimType.FillHorizontal, False)

def score_setup_display(game: 'MidiMaster', gui: 'Gui', controls_pos: Coord2d):
    trophy_size = Coord2d(0.175, 0.175 * game.window_ratio)
    trophy_pos = controls_pos - Coord2d(0.75, 0.0)
    score_pos = trophy_pos - Coord2d(0.55, 0.1)

    # Referenced by particle vfx attractor positions
    game.trophy_positions = [
        trophy_pos - Coord2d(0.15, 0.0),
        trophy_pos,
        trophy_pos + Coord2d(0.15, 0.0),
    ]

    # Create trophy widgets (gold, platinum, diamond)
    game.trophy = []
    for i in range(3):
        game.trophy.append(
            gui.add_create_widget(game.textures.create_sprite_texture(f"trophy{i+1}.png", game.trophy_positions[i], trophy_size, wrap=False))
        )
        trophy_anim = game.trophy[i].animate(AnimType.FillRadial)
        trophy_anim.reset(time=0.5)
        trophy_anim.active = True
        trophy_anim.loop = False

    game.score_bar = gui.add_create_widget(game.textures.create_sprite_texture("score_bg.tga", score_pos, Coord2d(0.6, 0.25)))
    game.score_bar.set_align(Alignment(AlignX.Centre, AlignY.Bottom))
    score_bar_anim = game.score_bar.animate(AnimType.FillHorizontal)
    score_bar_anim.reset(time=0.5)

def score_vfx(game: 'MidiMaster', note_id: int = None):
    game.score_fade = 1.0
    if note_id is not None:
        spawn_pos = [-0.71, game.staff.note_positions[note_id]]
        game.particles.spawn(2.0, spawn_pos, [0.37, 0.82, 0.4, 1.0], 1.0, game.trophy_positions[0].to_list(), 3)

def score_continuous_update(game: 'MidiMaster', dt: float):
    """Award score continuously for held notes."""
    if not game.music_running:
        return

    game.score_vfx_timer += dt
    should_trigger_vfx = game.score_vfx_timer >= 0.1

    scoring_happened = False
    active_note_id = None

    for note_id, note_info in game.active_scorable_notes.items():
        is_holding = note_id in game.player_notes_down

        if is_holding and note_info['player_started'] is not None:
            note_length = note_info['end_time'] - note_info['start_time']

            # Calculate required hold duration to get full points
            required_hold_duration = note_length * REQUIRED_HOLD_FRACTION
            score_rate = MAX_SCORE_PER_NOTE / required_hold_duration

            # Convert dt to 32nd notes
            from song import Song
            tempo_factor = game.music.tempo_bpm / 60.0  # Beats per second
            dt_in_32nds = dt * Song.SDQNotesPerBeat * tempo_factor

            # Award points for this frame
            points_this_frame = score_rate * dt_in_32nds

            # Cap to prevent over-scoring
            remaining = MAX_SCORE_PER_NOTE - note_info['score_earned']
            points_this_frame = min(points_this_frame, remaining)

            if points_this_frame > 0:
                note_info['score_earned'] += points_this_frame
                game.score += points_this_frame
                scoring_happened = True
                active_note_id = note_id

                # Update only the current active trophy (gold -> platinum -> diamond)
                trophy_thresholds = [r * game.score_max for r in TROPHY_SCORE]
                for i in range(3):
                    threshold = trophy_thresholds[i]
                    if game.score < threshold:
                        frac = game.score / max(threshold, 1.0)
                        game.trophy[i].animation.active = False
                        game.trophy[i].animation.frac = frac
                        game.trophy[i].animation.set_animation(AnimType.FillRadial, True)
                        break
                    else:
                        game.trophy[i].animation.frac = 1.0
                        game.trophy[i].animation.loop = True
                        game.trophy[i].animation.active = True
                        game.trophy[i].animation.set_animation(AnimType.Throb, True)

    # Trigger VFX once every 0.1s while scoring
    if scoring_happened and should_trigger_vfx and active_note_id is not None:
        score_vfx(game, active_note_id)
        game.score_vfx_timer = 0.0

def score_update_draw(game: 'MidiMaster', dt: float):
    game.score_bar.animation.frac = 0.43 + (0.57 * (game.score / max(game.score_max, 1.0)))
    game.score_fade = max(0.0, game.score_fade - (dt * 1.25))
    game.font_game.draw(f"{math.floor(game.score)}/{game.score_max} XP", 20, game.score_bar.sprite.pos - Coord2d(0.025, 0.03), [0.1, 0.1, 0.1, 1.0])
