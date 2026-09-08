"""Career venue set assignment: one progression per set, titled by style."""

import re

from procedural_songs import (
    BAR_32NDS,
    COUNT_IN_32NDS,
    DEGREE_PROGRESSIONS,
    PITCH_END,
    PITCH_START,
    TIER_CONFIGS,
    career_progress,
    chord_tone_degrees,
    format_set_title,
    generate_venue_album,
    pitch_window,
    progression_for_set,
    regenerate_set,
    rhythm_profile,
    scale_pitch_classes,
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
    title = format_set_title(0, "1564", "C")
    assert title == "Set 1 in C - Pop I-V-vi-IV"
    assert re.match(r"Set (\d+)", title).group(1) == "1"
    assert format_set_title(4, "36251", "C") == "Set 5 in C - Turnaround iii-vi-ii-V-I"
    assert format_set_title(0, "145", "G") == "Set 1 in G - Classic I-IV-V-I"


def test_score_key_still_parses_set_index():
    class _Song:
        artist = "Open Mic Night"
        title = "Set 3 in C - Doo-wop I-vi-IV-V"
        path = ""

        def get_name(self):
            return f"{self.artist} - {self.title}"

    assert SongBook.score_key(_Song()) == "venue:1:2"


def test_generated_album_titles_and_degrees_match():
    name, songs = generate_venue_album(1)
    assert name == "Open Mic Night"
    assert [s.title for s in songs] == [
        "Set 1 in C - Classic I-IV-V-I",
        "Set 2 in C - Pop I-V-vi-IV",
        "Set 3 in C - Doo-wop I-vi-IV-V",
        "Set 4 in C - Minor pop vi-IV-I-V",
    ]
    assert songs[0].get_name() == "Set 1 in C - Classic I-IV-V-I"
    assert name not in songs[0].get_name()
    assert songs[0].backing_degrees == [1, 4, 5, 1]
    assert songs[1].backing_degrees == [1, 5, 6, 4]


def test_regenerate_keeps_the_same_progression():
    original = generate_venue_album(3)[1][0]
    retry = regenerate_set(3, 0)
    assert original.title == retry.title == "Set 1 in C - Jazz ii-V-I"
    assert original.backing_degrees == retry.backing_degrees == [2, 5, 1]


def test_regenerate_resets_existing_song_in_place():
    from procedural_songs import rng

    rng.seed(1)
    song = generate_venue_album(5)[1][-1]
    original_notes = [(n.note, n.time, n.length) for n in song.notes]
    degrees = list(song.backing_degrees)
    artist = song.artist
    score = dict(song.score)

    rng.seed(2)
    same = regenerate_set(5, TIER_CONFIGS[5]["num_sets"] - 1, song)
    assert same is song
    assert song.artist == artist
    assert song.score == score
    assert song.backing_degrees == degrees
    assert song.notes
    assert [(n.note, n.time, n.length) for n in song.notes] != original_notes


def test_world_tour_covers_every_progression():
    names = [
        progression_for_set(TIER_CONFIGS[5], i)
        for i in range(TIER_CONFIGS[5]["num_sets"])
    ]
    assert set(names) == set(DEGREE_PROGRESSIONS)


def test_career_progress_ramps_across_venues():
    assert career_progress(1, 0) == 0.0
    assert career_progress(5, TIER_CONFIGS[5]["num_sets"] - 1) == 1.0
    assert career_progress(1, 0) < career_progress(3, 0) < career_progress(5, 0)
    assert pitch_window(0.0) == PITCH_START
    assert pitch_window(1.0) == PITCH_END
    early_lo, early_hi = pitch_window(0.0)
    late_lo, late_hi = pitch_window(1.0)
    assert late_lo < early_lo
    assert late_hi > early_hi
    assert 32 in rhythm_profile(0.0)[0]
    assert 2 in rhythm_profile(1.0)[0]


def _has_note_gap(song):
    ordered = sorted(song.notes, key=lambda n: n.time)
    return any(b.time > a.time + a.length for a, b in zip(ordered, ordered[1:]))


def test_generated_songs_leave_gaps_for_rests():
    from procedural_songs import rng

    rng.seed(11)
    assert any(
        _has_note_gap(song)
        for tier in TIER_CONFIGS
        for song in generate_venue_album(tier)[1]
    )


def _bar_end_notes(song):
    ends = []
    for note in song.notes:
        end = note.time + note.length
        if (end - COUNT_IN_32NDS) % BAR_32NDS == 0:
            ends.append(note)
    return ends


def test_open_mic_stays_near_the_clef_on_whole_notes():
    first = generate_venue_album(1)[1][0]
    lo, hi = pitch_window(0.0)
    assert first.notes
    assert all(lo <= n.note <= hi for n in first.notes)
    assert all(n.length == 32 for n in first.notes)
    assert first.notes[0].time == COUNT_IN_32NDS


def test_world_tour_finale_uses_wider_range_and_sixteenths():
    finale = generate_venue_album(5)[1][-1]
    lo, hi = pitch_window(1.0)
    assert any(n.length == 2 for n in finale.notes)
    assert all(lo <= n.note <= hi for n in finale.notes)
    assert hi - lo > pitch_window(0.0)[1] - pitch_window(0.0)[0]


def test_bar_endings_are_chord_tones():
    song = generate_venue_album(2)[1][0]
    scale = scale_pitch_classes(song.key_signature)
    degrees = song.backing_degrees
    for note in _bar_end_notes(song):
        bar = (note.time - COUNT_IN_32NDS) // BAR_32NDS
        roman = degrees[bar % len(degrees)]
        chord_pcs = {scale[d] for d in chord_tone_degrees(roman)}
        assert note.note % 12 in chord_pcs
        # Landing tone is at least as long as a quarter
        assert note.length >= 8
