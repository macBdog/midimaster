"""Unit tests for backing time/degree helpers (no audio device required)."""

from backing import (
    bar_index_from_samples,
    degree_for_bar,
    music_time_to_seconds,
    music_time_to_samples,
    _read_loop,
)
import numpy as np


def test_bar_index_from_samples():
    spb = 105840  # 2.4s * 44100
    assert bar_index_from_samples(0, spb) == 0
    assert bar_index_from_samples(spb - 1, spb) == 0
    assert bar_index_from_samples(spb, spb) == 1
    assert bar_index_from_samples(spb * 3 + 5, spb) == 3


def test_degree_for_bar_cycles_progression():
    prog = [1, 4, 5, 1]
    assert degree_for_bar(0, prog) is None
    assert degree_for_bar(1, prog) == 1
    assert degree_for_bar(2, prog) == 4
    assert degree_for_bar(3, prog) == 5
    assert degree_for_bar(4, prog) == 1
    assert degree_for_bar(5, prog) == 1  # wrap


def test_degree_251():
    prog = [2, 5, 1]
    assert degree_for_bar(1, prog) == 2
    assert degree_for_bar(2, prog) == 5
    assert degree_for_bar(3, prog) == 1
    assert degree_for_bar(4, prog) == 2


def test_music_time_to_seconds_100bpm():
    # 1 bar = 32 thirty-seconds at 100 BPM → 2.4 s
    assert abs(music_time_to_seconds(32, 100) - 2.4) < 1e-9
    assert abs(music_time_to_seconds(0, 100)) < 1e-12
    assert music_time_to_samples(32, 100, 44100) == int(2.4 * 44100)


def test_read_loop_wraps():
    buf = np.arange(10, dtype=np.float32).reshape(5, 2)
    # start near end, wrap 3 frames
    out = _read_loop(buf, start=4, frames=3)
    assert out.shape == (3, 2)
    np.testing.assert_array_equal(out[0], buf[4])
    np.testing.assert_array_equal(out[1], buf[0])
    np.testing.assert_array_equal(out[2], buf[1])
