"""Unit tests for backing time/degree helpers (no audio device required)."""

from pathlib import Path

from backing import (
    bar_index_from_samples,
    bass_filename,
    choose_comp_instrument,
    COMP_CHOICES,
    comp_choice_label,
    comp_filename,
    degree_for_bar,
    discover_comp_instruments,
    harmonic_stems_present,
    key_dir,
    key_token,
    resolve_audio,
    resolve_comp_choice,
    music_time_to_seconds,
    music_time_to_samples,
    parse_comp_stem,
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


def test_key_token():
    assert key_token("C") == "c"
    assert key_token("F#") == "fs"
    assert key_token("Gm") == "gm"
    assert key_token(None) == "c"


def test_stem_filenames():
    assert bass_filename(4) == "bass_4.flac"
    assert comp_filename("guitar", 6) == "comp_guitar_6.flac"
    assert comp_filename("ep", 1) == "comp_ep_1.flac"
    assert key_dir(Path("assets/backing"), "C") == Path("assets/backing/c")
    assert key_dir(Path("assets/backing"), "F#") == Path("assets/backing/fs")


def test_parse_comp_stem():
    assert parse_comp_stem("comp_ep_1.flac") == ("ep", 1)
    assert parse_comp_stem("comp_guitar_6.wav") == ("guitar", 6)
    assert parse_comp_stem("comp_rhodes_mk1_2.flac") == ("rhodes_mk1", 2)
    assert parse_comp_stem("comp_1.flac") is None
    assert parse_comp_stem("bass_1.flac") is None


def test_discover_and_choose_comp(tmp_path):
    (tmp_path / "c").mkdir()
    (tmp_path / "g").mkdir()
    (tmp_path / "c" / "comp_ep_1.flac").write_bytes(b"")
    (tmp_path / "c" / "comp_guitar_1.flac").write_bytes(b"")
    (tmp_path / "c" / "bass_1.flac").write_bytes(b"")
    (tmp_path / "g" / "comp_guitar_1.wav").write_bytes(b"")
    assert discover_comp_instruments(tmp_path, "C") == ["ep", "guitar"]
    assert discover_comp_instruments(tmp_path, "G") == ["guitar"]
    assert choose_comp_instrument(["ep", "guitar"]) == "guitar"
    assert choose_comp_instrument(["ep", "guitar"], preferred="ep") == "ep"
    assert choose_comp_instrument(["ep"]) == "ep"
    assert harmonic_stems_present(tmp_path, "C")
    assert not harmonic_stems_present(tmp_path, "F")
    assert resolve_audio(tmp_path / "c", "bass_1").name == "bass_1.flac"
    (tmp_path / "c" / "bass_2.wav").write_bytes(b"")
    assert resolve_audio(tmp_path / "c", "bass_2").name == "bass_2.wav"
    (tmp_path / "c" / "bass_1.wav").write_bytes(b"")
    assert resolve_audio(tmp_path / "c", "bass_1").suffix == ".flac"


def test_key_folder_symlink_reuse(tmp_path):
    (tmp_path / "c").mkdir()
    (tmp_path / "g").mkdir()
    src = tmp_path / "c" / "bass_6.flac"
    src.write_bytes(b"am7")
    dest = tmp_path / "g" / "bass_2.flac"
    try:
        dest.symlink_to(Path("..") / "c" / "bass_6.flac")
    except OSError:
        return
    resolved = resolve_audio(tmp_path / "g", "bass_2")
    assert resolved is not None
    assert resolved.read_bytes() == b"am7"
    assert harmonic_stems_present(tmp_path, "G")


def test_resolve_comp_choice():
    assert resolve_comp_choice("off", ["ep", "guitar"], "guitar") is None
    assert resolve_comp_choice("auto", ["ep", "guitar"], "guitar") == "guitar"
    assert resolve_comp_choice("guitar", ["ep", "guitar"]) == "guitar"
    assert resolve_comp_choice("ep", ["ep", "guitar"]) == "ep"
    assert resolve_comp_choice("auto", ["ep", "guitar"], "ep") == "ep"
    assert comp_choice_label("ep") == "Electric Piano"
    assert set(COMP_CHOICES) == {"auto", "ep", "guitar", "off"}
