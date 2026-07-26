"""Fundamental-frequency / melody tracking and tempo estimation (librosa)."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

import numpy as np

# Analysis defaults
DEFAULT_SR = 22050
HOP_LENGTH = 256
FRAME_LENGTH = 2048
FMIN_HZ = 65.0   # ~C2
FMAX_HZ = 2100.0  # ~C7

# Prefer mid-tempo pop/electronic range when correcting half/double-time errors
_BPM_PREF_LO = 70.0
_BPM_PREF_HI = 160.0


def _require_librosa():
    try:
        import librosa
    except ImportError as exc:
        raise ImportError(
            "audio_to_midi requires librosa (and soundfile). Install with:\n"
            "  pip install -r utils/audio_to_midi/requirements.txt"
        ) from exc
    return librosa


def load_audio(
    path: Union[str, Path],
    *,
    sr: int = DEFAULT_SR,
    mono: bool = True,
) -> Tuple[np.ndarray, int]:
    """Load an audio file as float32 mono at *sr* via librosa."""
    librosa = _require_librosa()
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    y, file_sr = librosa.load(str(path), sr=sr, mono=mono)
    return np.asarray(y, dtype=np.float32), int(file_sr)


def estimate_f0(
    audio: np.ndarray,
    sr: int,
    *,
    fmin: float = FMIN_HZ,
    fmax: float = FMAX_HZ,
    hop_length: int = HOP_LENGTH,
    frame_length: int = FRAME_LENGTH,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return ``(times_sec, f0_hz)`` for analysis frames.

    Unvoiced / silent frames use ``f0_hz == 0``. Uses librosa.pyin.
    """
    librosa = _require_librosa()
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if audio.size == 0:
        return np.zeros(0, dtype=np.float64), np.zeros(0, dtype=np.float64)

    f0, voiced_flag, _ = librosa.pyin(
        audio,
        fmin=fmin,
        fmax=fmax,
        sr=sr,
        hop_length=hop_length,
        frame_length=frame_length,
    )
    f0 = np.asarray(f0, dtype=np.float64)
    voiced = np.asarray(voiced_flag, dtype=bool)
    f0 = np.where(np.isnan(f0) | ~voiced, 0.0, f0)
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    return np.asarray(times, dtype=np.float64), f0


def _as_scalar_tempo(tempo) -> float:
    arr = np.atleast_1d(np.asarray(tempo, dtype=np.float64))
    if arr.size == 0 or not np.isfinite(arr[0]) or arr[0] <= 0:
        return 0.0
    return float(arr[0])


def _normalize_tempo_octave(bpm: float) -> float:
    """Fold BPM into a musically common range by ×2 / ÷2 (half/double-time)."""
    if bpm <= 0 or not np.isfinite(bpm):
        return 0.0
    while bpm < _BPM_PREF_LO and bpm * 2.0 <= 240.0:
        bpm *= 2.0
    while bpm > _BPM_PREF_HI and bpm / 2.0 >= 40.0:
        bpm /= 2.0
    return bpm


def pin_bpm(bpm: float) -> float:
    """
    Snap tempo to a stable value for MIDI export.

    Rounds to one decimal place (e.g. 107.7) after half/double correction.
    """
    bpm = _normalize_tempo_octave(float(bpm))
    if bpm <= 0:
        return 120.0
    return round(bpm, 1)


def estimate_bpm(audio: np.ndarray, sr: int) -> float:
    """
    Auto-detect and pin a global tempo for the clip.

    Uses librosa onset strength + beat tracking, with half/double-time
    correction and decimal pinning. Always returns a positive BPM.
    """
    librosa = _require_librosa()
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if audio.size < sr // 4:
        return 120.0

    hop = 512
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)

    # Primary: beat tracker global tempo
    tempo, _beats = librosa.beat.beat_track(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop,
        units="frames",
    )
    candidates = [_as_scalar_tempo(tempo)]

    # Secondary: tempo histogram peak (helps on electronic material)
    try:
        if hasattr(librosa.feature, "tempo"):
            tg = librosa.feature.tempo(
                onset_envelope=onset_env,
                sr=sr,
                hop_length=hop,
                aggregate=None,
            )
            tg = np.asarray(tg, dtype=np.float64).reshape(-1)
            tg = tg[np.isfinite(tg) & (tg > 0)]
            if tg.size:
                # Mode via histogram
                hist, edges = np.histogram(tg, bins=48, range=(40.0, 240.0))
                peak = int(np.argmax(hist))
                candidates.append(float(0.5 * (edges[peak] + edges[peak + 1])))
                candidates.append(float(np.median(tg)))
    except Exception:
        pass

    # Score candidates: prefer mid-range after octave fold, higher prior on beat_track
    best = 120.0
    best_score = -1.0
    for i, raw in enumerate(candidates):
        if raw <= 0:
            continue
        folded = _normalize_tempo_octave(raw)
        # Distance from sweet spot ~110–120
        center = 115.0
        score = 1.0 / (1.0 + abs(folded - center) / 40.0)
        if i == 0:
            score += 0.35  # prefer beat_track estimate
        if score > best_score:
            best_score = score
            best = folded

    return pin_bpm(best)
