import math
from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.widget import Alignment, AlignX, AlignY

from menu_func import game_score_bg_colour, TROPHY_SCORE

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from midimaster import MidiMaster
    from gamejam.gui import Gui


def calculate_max_score_for_note(note_length_32nds: float) -> float:
    """Calculate maximum possible score for a note.

    Args:
        note_length_32nds: Note duration in 32nd notes

    Returns:
        Max score (float)
    """
    # Base score scales with note length
    # Whole note (128 32nds) = 100 points
    # Quarter note (32 32nds) = 25 points
    # Eighth note (16 32nds) = 12.5 points
    base_score = (note_length_32nds / 128.0) * 100.0
    return max(base_score, 5.0)  # Minimum 5 points per note

def score_reset_ui(game: 'MidiMaster'):
    """Reset all score UI elements for a new song."""
    # Reset trophy animations to empty state
    for i in range(3):
        if hasattr(game, 'tally') and len(game.tally) > i:
            tally_anim = game.tally[i].animation
            tally_anim.time = 1
            tally_anim.frac = 0.0
            tally_anim.mag = 1.0
            tally_anim.set_animation(AnimType.FillRadial, False)

    # Reset score bar to empty
    if hasattr(game, 'score_bar') and game.score_bar:
        score_bar_anim = game.score_bar.animation
        score_bar_anim.time = -1
        score_bar_anim.frac = 0.0
        score_bar_anim.set_animation(AnimType.FillHorizontal, False)

def score_setup_display(game: 'MidiMaster', gui: 'Gui', controls_pos: Coord2d):
    tally_size = Coord2d(0.175, 0.175 * game.window_ratio)
    tally_pos = controls_pos - Coord2d(0.75, 0.0)
    score_pos = tally_pos - Coord2d(0.55, 0.1)

    # Referenced by vfx attractor pos
    game.tally_positions = [
        tally_pos - Coord2d(0.15, 0.0),
        tally_pos,
        tally_pos + Coord2d(0.15, 0.0),
    ]

    game.tally = []
    for i in range(3):
        game.tally.append(
            gui.add_create_widget(game.textures.create_sprite_texture(f"trophy{i+1}.png", game.tally_positions[i], tally_size, wrap=False))
        )
        tally_anim = game.tally[i].animate(AnimType.FillRadial)
        tally_anim.time = 1
        tally_anim.frac = 0.0
        tally_anim.mag = 1.0
        tally_anim.loop = False

    game.bg_score = gui.add_create_widget(game.textures.create("score_bg.tga", score_pos, Coord2d(0.5, 0.25)))
    game.bg_score.set_colour_func(game_score_bg_colour, {"game":game})
    game.bg_score.set_align(Alignment(AlignX.Centre, AlignY.Bottom))

    score_bar_size = Coord2d(0.32, 0.07)
    game.score_bar = gui.add_create_widget(game.textures.create_sprite_texture("score_bar.png", score_pos + Coord2d(0.12, 0.05), score_bar_size))
    score_bar_anim = game.score_bar.animate(AnimType.FillHorizontal)
    score_bar_anim.time = -1
    score_bar_anim.frac = 0.0

def score_vfx(game: 'MidiMaster', note_id: int = None):
    game.score_fade = 1.0
    game.menu.set_event("score_vfx")
    if note_id is not None:
        spawn_pos = [-0.71, game.staff.note_positions[note_id]]
        game.particles.spawn(2.0, spawn_pos, [0.37, 0.82, 0.4, 1.0], 1.0, game.tally_positions[0].to_list())

def score_playable_note_on(game: 'MidiMaster', note):
    trophies = [r * game.score_max for r in TROPHY_SCORE]
    for i in range(3):
        frac = game.score / max(trophies[i], 1.0)
        anim_type = AnimType.Throb if frac >= 1.0 else AnimType.FillRadial
        game.tally[i].animation.frac = frac
        game.tally[i].animation.mag = 1.0
        game.tally[i].animation.time = -1
        game.tally[i].animation.set_animation(anim_type, True)

def score_player_note_on(game: 'MidiMaster', message):
    if message.note in game.scored_notes:
        score_vfx(game, message.note)
        time_diff = game.music_time - game.scored_notes[message.note]
        game.score += 10 - min(time_diff, 9)
        game.score_bar.animation.frac = game.score / max(game.score_max, 1.0)
        del game.scored_notes[message.note]

def score_continuous_update(game: 'MidiMaster', dt: float):
    """Award score continuously for held notes.

    Called every frame from midimaster.update().
    Awards points proportional to:
    - Delta time (dt)
    - Note accuracy (how well timed the press was)
    - Sustain quality (continuous hold without gaps)
    """
    if not game.music_running:
        return  # Don't accumulate score while paused

    for note_id, note_info in game.active_scorable_notes.items():
        # Check if player is currently holding this note
        is_holding = note_id in game.player_notes_down

        if is_holding and note_info['player_started'] is not None:
            # Calculate scoring rate
            note_length = note_info['end_time'] - note_info['start_time']
            max_score = note_info['max_possible']

            # Base score rate (points per 32nd note)
            # Convert note_length from 32nd notes to seconds for rate calculation
            if note_length > 0:
                base_rate = max_score / max(note_length, 1.0)
            else:
                base_rate = max_score

            # Accuracy multiplier (based on timing of initial press)
            time_diff = abs(note_info['player_started'] - note_info['start_time'])
            accuracy = max(0.5, 1.0 - (time_diff / 2.0))  # 50% to 100%

            # Award points (dt is in seconds, need to convert to 32nd notes)
            # Assuming 120 BPM: 1 beat = 0.5 seconds, 1 32nd = 0.5/8 = 0.0625 seconds
            from song import Song
            tempo_factor = game.music.tempo_bpm / 60.0  # Beats per second
            dt_in_32nds = dt * Song.SDQNotesPerBeat * tempo_factor

            points_this_frame = base_rate * accuracy * dt_in_32nds

            # Cap to prevent over-scoring
            remaining = max_score - note_info['score_earned']
            points_this_frame = min(points_this_frame, remaining)

            if points_this_frame > 0:
                note_info['score_earned'] += points_this_frame
                game.score += points_this_frame

                # Update trophy animations
                trophies = [r * game.score_max for r in TROPHY_SCORE]
                for i in range(3):
                    frac = game.score / max(trophies[i], 1.0)
                    anim_type = AnimType.Throb if frac >= 1.0 else AnimType.FillRadial
                    game.tally[i].animation.frac = frac
                    game.tally[i].animation.set_animation(anim_type, True)


def score_update_draw(game: 'MidiMaster', dt: float):
    if game.staff.is_scoring():
        if game.score_fade < 0.5:
            for note in game.scored_notes:
                score_vfx(game, note)
                break

    # Update score bar
    game.score_bar.animation.frac = game.score / max(game.score_max, 1.0)

    game.score_fade -= dt * 0.5
    game.font_game.draw(f"{math.floor(game.score)}/{game.score_max} XP", 20, game.bg_score.sprite.pos - Coord2d(0.025, 0.03), [0.1, 0.1, 0.1, 1.0])
