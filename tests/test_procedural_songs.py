"""Career venue set assignment: one progression per set, titled by style."""

import re

from procedural_songs import (
    DEGREE_PROGRESSIONS,
    TIER_CONFIGS,
    format_set_title,
    generate_venue_album,
    progression_for_set,
    regenerate_set,
)
from song_book import SongBook


def test_each_set_has_a_distinct_progression():
    for tier, config in TIER_CONFIGS.items():
        names = [
            progression_for_set(config, i) for i in range(config["num_sets"])
        ]
        assert len(names) == config["num_sets"]
        assert len(set(names)) == len(names), f"tier {tier} repeats: {names}"
        for name in names:
            assert name in DEGREE_PROGRESSIONS


def test_set_titles_name_the_style_and_keep_score_prefix():
    title = format_set_title(0, "1564")
    assert title == "Set 1: Pop I-V-vi-IV"
    assert re.match(r"Set (\d+)", title).group(1) == "1"
    assert format_set_title(4, "36251") == "Set 5: Turnaround iii-vi-ii-V-I"


def test_score_key_still_parses_set_index():
    class _Song:
        artist = "Open Mic Night"
        title = "Set 3: Doo-wop I-vi-IV-V"
        path = ""

        def get_name(self):
            return f"{self.artist} - {self.title}"

    assert SongBook.score_key(_Song()) == "venue:1:2"


def test_generated_album_titles_and_degrees_match():
    name, songs = generate_venue_album(1)
    assert name == "Open Mic Night"
    assert [s.title for s in songs] == [
        "Set 1: Classic I-IV-V-I",
        "Set 2: Pop I-V-vi-IV",
        "Set 3: Doo-wop I-vi-IV-V",
        "Set 4: Minor pop vi-IV-I-V",
    ]
    assert songs[0].backing_degrees == [1, 4, 5, 1]
    assert songs[1].backing_degrees == [1, 5, 6, 4]


def test_regenerate_keeps_the_same_progression():
    original = generate_venue_album(3)[1][0]
    retry = regenerate_set(3, 0)
    assert original.title == retry.title == "Set 1: Jazz ii-V-I"
    assert original.backing_degrees == retry.backing_degrees == [2, 5, 1]


def test_world_tour_covers_every_progression():
    names = [
        progression_for_set(TIER_CONFIGS[5], i)
        for i in range(TIER_CONFIGS[5]["num_sets"])
    ]
    assert set(names) == set(DEGREE_PROGRESSIONS)
