"""Fundamental-frequency / melody tracking (TODO)."""

from __future__ import annotations

from typing import Tuple

import numpy as np


def estimate_f0(audio: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return (times_sec, f0_hz) for voiced frames.

    Placeholder — wire librosa.pyin or CREPE here.
    """
    raise NotImplementedError("pitch_track.estimate_f0")
