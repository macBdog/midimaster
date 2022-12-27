import math
from gamejam.animation import AnimType
from gamejam.coord import Coord2d
from gamejam.widget import Alignment, AlignX, AlignY

from menu_func import MusicMode, game_score_bg_colour

def score_setup_display(game, gui, controls_pos_y):
    trophy_size = Coord2d(0.175, 0.175 * game.window_ratio)

    game.trophy_positions = [
        Coord2d(-0.15, controls_pos_y),
        Coord2d(0.0, controls_pos_y),
        Coord2d(0.15, controls_pos_y),
    ]
    game.trophy1 = gui.add_create_widget(game.textures.create_sprite_texture("trophy1.png", game.trophy_positions[0], trophy_size, wrap=False))
    trophy1_anim = game.trophy1.animate(AnimType.FillRadial)
    trophy1_anim.time = -1
    trophy1_anim.frac = 0.0

    game.trophy2 = gui.add_create_widget(game.textures.create_sprite_texture("trophy2.png", game.trophy_positions[1], trophy_size, wrap=False))
    trophy2_anim = game.trophy2.animate(AnimType.FillRadial)
    trophy2_anim.time = -1
    trophy2_anim.frac = 0.0

    game.trophy3 = gui.add_create_widget(game.textures.create_sprite_texture("trophy3.png", game.trophy_positions[2], trophy_size, wrap=False))
    trophy3_anim = game.trophy3.animate(AnimType.FillRadial)
    trophy3_anim.time = -1
    trophy3_anim.frac = 0.0

    score_pos_x = -0.53
    game.bg_score = gui.add_create_widget(game.textures.create_sprite_texture("score_bg.tga", Coord2d(score_pos_x, controls_pos_y - 0.10), Coord2d(0.5, 0.25)))
    game.bg_score.set_colour_func(game_score_bg_colour, {"game":game})
    game.bg_score.set_align(Alignment(AlignX.Centre, AlignY.Bottom))

    game.score_bar = gui.add_create_widget(game.textures.create_sprite_texture("gui/panel_long.png", Coord2d(score_pos_x, controls_pos_y - 0.15), Coord2d(0.2, 0.1)))
    score_bar_anim = game.score_bar.animate(AnimType.FillHorizontal)
    score_bar_anim.time = -1
    score_bar_anim.frac = 0.0

def score_vfx(game, note_id:int = None):
    game.score_fade = 1.0
    game.menu.set_event("score_vfx")
    if note_id is not None:
        spawn_pos = [-0.71, game.staff.note_positions[note_id]]
        game.particles.spawn(2.0, spawn_pos, [0.37, 0.82, 0.4, 1.0], 1.0, game.trophy_positions[0].to_list())


def score_player_note_on(game, message):
    if game.mode == MusicMode.PAUSE_AND_LEARN:
        if message.note in game.scored_notes:
            score_vfx(game, message.note)
            time_diff = game.music_time - game.scored_notes[message.note]
            game.score += max(10 - time_diff, 0)
            game.score_bar.animation.frac = game.score / 1000
            del game.scored_notes[message.note]


def score_update(game, dt, music_time_advance):
    if game.mode == MusicMode.PERFORMANCE:
        if game.staff.is_scoring():
            if game.score_fade < 0.5:
                for note in game.scored_notes:
                    score_vfx(note)
                    break
            game.score += 10 ** dt
            game.score_bar.animation.frac = game.score / 2000
    elif game.mode == MusicMode.PAUSE_AND_LEARN:
        if len(game.scored_notes) > 0 and game.music_running:
            game.music_time -= music_time_advance


def score_draw(game, dt):
    game.score_fade -= dt * 0.5
    game.font_game.draw(f"{math.floor(game.score)} XP", 22, game.bg_score.sprite.pos - Coord2d(0.025, 0.03), [0.1, 0.1, 0.1, 1.0])
