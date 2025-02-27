import math
from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.widget import Alignment, AlignX, AlignY

from menu_func import MusicMode, game_score_bg_colour

def score_setup_display(game, gui, controls_pos: Coord2d):
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
        tally_anim.time = -1
        tally_anim.frac = 0.0
        tally_anim.mag = 1.0

    game.bg_score = gui.add_create_widget(game.textures.create("score_bg.tga", score_pos, Coord2d(0.5, 0.25)))
    game.bg_score.set_colour_func(game_score_bg_colour, {"game":game})
    game.bg_score.set_align(Alignment(AlignX.Centre, AlignY.Bottom))

    score_bar_size = Coord2d(0.32, 0.07)
    game.score_bar = gui.add_create_widget(game.textures.create_sprite_texture("score_bar.png", score_pos + Coord2d(0.12, 0.05), score_bar_size))
    score_bar_anim = game.score_bar.animate(AnimType.FillHorizontal)
    score_bar_anim.time = -1
    score_bar_anim.frac = 0.0


def score_vfx(game, note_id:int = None):
    game.score_fade = 1.0
    game.menu.set_event("score_vfx")
    if note_id is not None:
        spawn_pos = [-0.71, game.staff.note_positions[note_id]]
        game.particles.spawn(2.0, spawn_pos, [0.37, 0.82, 0.4, 1.0], 1.0, game.tally_positions[0].to_list())


def score_playable_note_on(game, note):
    for i in range(3):
        game.tally[i].animation.frac = 1.0
        game.tally[i].animation.mag = 1.0
        game.tally[i].animation.set_animation(AnimType.FillRadial, True)


def score_player_note_on(game, message):
    if game.mode == MusicMode.PAUSE_AND_LEARN:
        if message.note in game.scored_notes:
            score_vfx(game, message.note)
            time_diff = game.music_time - game.scored_notes[message.note]
            game.score += max(10 - time_diff, 0)
            game.score_bar.animation.frac = game.score / 1000
            del game.scored_notes[message.note]

            for i in range(3):
                if game.tally[i].animation.frac > 0.0:
                    game.tally[i].animation.set_animation(AnimType.Flash, True)
                    game.tally[i].animation.mag = 8.0
                    game.tally[i].animation.frac = 1.0
                else:
                    game.tally[i].animation.set_animation(AnimType.FadeOut)


def score_update_draw(game, dt):
    if game.mode == MusicMode.PERFORMANCE:
        if game.staff.is_scoring():
            if game.score_fade < 0.5:
                for note in game.scored_notes:
                    score_vfx(note)
                    break
            game.score += 10 ** dt
            game.score_bar.animation.frac = game.score / 2000
    elif game.mode == MusicMode.PAUSE_AND_LEARN:
        for i in range(3):
            idx = i + 1
            game.tally[i].animation.frac = max(game.tally[i].animation.frac - (dt * idx * 0.5), 0.0)

    game.score_fade -= dt * 0.5
    #game.font_game.draw(f"{math.floor(game.score)} XP", 22, game.bg_score.sprite.pos - Coord2d(0.025, 0.03), [0.1, 0.1, 0.1, 1.0])
