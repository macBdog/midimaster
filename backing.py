"""Runtime audio backing: 1-bar stem loops mixed and synced to transport.

Expects stems under assets/backing/ (see assets/backing/STEMS.md).
Minimal kit: count_in.wav + drums.wav. Bass/comp per degree are optional.

Transport: free-running sample playhead in the audio callback (no per-frame
re-seek from game time — that causes crackle). Game sets playhead only on
start, pause, rewind, or a large seek. Stems authored at NATIVE_BPM play with
no time-stretch when the song tempo matches.
"""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np

from song import Song

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:  # pragma: no cover
    sd = None
    sf = None

NATIVE_BPM = 100.0
# Only stretch when tempo differs by more than this (BPM)
STRETCH_EPSILON_BPM = 0.5
# Hard-seek if game and audio playheads diverge by more than this (seconds)
SEEK_SNAP_SECONDS = 0.25
BAR_32NDS = 32  # one 4/4 bar in Song.SDQNotesPerBeat units
_C100 = Path("assets") / "backing" / "c100"
_FLAT = Path("assets") / "backing"
DEFAULT_ASSETS = _C100 if (_C100 / "drums.wav").is_file() else _FLAT
DEGREES = (1, 2, 3, 4, 5, 6)


def music_time_to_seconds(music_time: float, tempo_bpm: float) -> float:
    """Convert 32nd-note music_time to seconds at tempo_bpm."""
    return music_time / (Song.SDQNotesPerBeat * (tempo_bpm / 60.0))

def music_time_to_samples(music_time: float, tempo_bpm: float, sample_rate: int) -> int:
    return int(music_time_to_seconds(music_time, tempo_bpm) * sample_rate)

def bar_index_from_samples(sample_pos: int, samples_per_bar: int) -> int:
    if sample_pos < 0 or samples_per_bar <= 0:
        return 0
    return int(sample_pos // samples_per_bar)

def degree_for_bar(bar: int, progression: list[int]) -> int | None:
    """Degree for a song bar. Bar 0 is count-in (None). After that, cycle progression."""
    if not progression or bar < 1:
        return None
    return progression[(bar - 1) % len(progression)]

def _to_stereo_f32(data: np.ndarray) -> np.ndarray:
    """Ensure float32 shape (n, 2)."""
    x = np.asarray(data, dtype=np.float32)
    if x.ndim == 1:
        x = np.column_stack([x, x])
    elif x.shape[1] == 1:
        x = np.column_stack([x[:, 0], x[:, 0]])
    elif x.shape[1] > 2:
        x = x[:, :2]
    return np.ascontiguousarray(x)

def _time_stretch(stereo: np.ndarray, rate: float) -> np.ndarray:
    """Time-stretch stereo without pitch change. rate>1 shortens (faster tempo)."""
    if abs(rate - 1.0) < 1e-3:
        return stereo
    import librosa

    channels = []
    for c in range(stereo.shape[1]):
        channels.append(librosa.effects.time_stretch(stereo[:, c], rate=rate))
    n = min(len(ch) for ch in channels)
    out = np.column_stack([ch[:n] for ch in channels]).astype(np.float32)
    return np.ascontiguousarray(out)

def _read_loop(buf: np.ndarray, start: int, frames: int) -> np.ndarray:
    """Circular read of frames from stereo buffer starting at sample index start."""
    n = buf.shape[0]
    if n == 0 or frames <= 0:
        return np.zeros((max(frames, 0), 2), dtype=np.float32)
    start %= n
    end = start + frames
    if end <= n:
        return buf[start:end]
    first = buf[start:]
    remain = frames - first.shape[0]
    parts = [first]
    while remain > 0:
        take = min(remain, n)
        parts.append(buf[:take])
        remain -= take
    return np.vstack(parts)

class Backing:
    """Minimal multi-stem mixer with continuous sample playhead."""

    def __init__(self, assets_root: Path | str | None = None):
        self.assets_root = Path(assets_root) if assets_root else DEFAULT_ASSETS
        self._lock = threading.Lock()
        self._stream = None
        self._running = False
        self._active = False
        self._sample_rate = 44100
        self._tempo_bpm = NATIVE_BPM
        self._samples_per_bar = 1
        self._playhead = 0  # samples from song start; advanced only in callback
        self._progression: list[int] = [1, 4, 5, 1]
        self._gain = 0.4

        self._count_in: np.ndarray | None = None
        self._drums: np.ndarray | None = None
        self._bass: dict[int, np.ndarray] = {}
        self._comp: dict[int, np.ndarray] = {}

    @property
    def active(self) -> bool:
        return self._active

    @property
    def tempo_bpm(self) -> float:
        return self._tempo_bpm

    def kit_present(self) -> bool:
        """True if minimal kit (count-in + drums) exists."""
        if sf is None or sd is None:
            return False
        root = self.assets_root
        return (root / "count_in.wav").is_file() and (root / "drums.wav").is_file()

    def load(self, song: Song) -> bool:
        """Load stems. No stretch when song tempo is native (100 BPM)."""
        self.stop()
        self._active = False
        self._count_in = None
        self._drums = None
        self._bass.clear()
        self._comp.clear()

        if not getattr(song, "use_audio_backing", False):
            return False
        if not getattr(song, "backing_degrees", None):
            return False
        if not self.kit_present():
            print(f"[backing] Minimal kit missing at {self.assets_root}; MIDI fallback.")
            return False

        # Stems are authored at 100 BPM. Game audio matches without stretch
        song_tempo = float(song.tempo_bpm) if song.tempo_bpm else NATIVE_BPM
        if abs(song_tempo - NATIVE_BPM) <= STRETCH_EPSILON_BPM:
            tempo = NATIVE_BPM
            stretch_rate = 1.0
        else:
            tempo = song_tempo
            stretch_rate = tempo / NATIVE_BPM

        try:
            count_in, sr = self._load_wav(self.assets_root / "count_in.wav")
            drums, sr_d = self._load_wav(self.assets_root / "drums.wav")
            if sr_d != sr:
                print("[backing] Sample rate mismatch (count_in vs drums); MIDI fallback.")
                return False

            ref_len = drums.shape[0]
            bass: dict[int, np.ndarray] = {}
            comp: dict[int, np.ndarray] = {}
            loaded_comp: list[int] = []
            loaded_bass: list[int] = []

            for d in DEGREES:
                bass_path = self.assets_root / f"bass_{d}.wav"
                comp_path = self.assets_root / f"comp_{d}.wav"
                if bass_path.is_file():
                    b, sr_b = self._load_wav(bass_path)
                    if sr_b != sr:
                        print(f"[backing] Skip bass_{d}: sample rate {sr_b} != {sr}")
                    else:
                        if abs(b.shape[0] - ref_len) > max(1, int(ref_len * 0.02)):
                            print(
                                f"[backing] Warn bass_{d}: {b.shape[0] / sr:.3f}s "
                                f"vs drums {ref_len / sr:.3f}s (loop length mismatch)"
                            )
                        bass[d] = b
                        loaded_bass.append(d)
                if comp_path.is_file():
                    c, sr_c = self._load_wav(comp_path)
                    if sr_c != sr:
                        print(f"[backing] Skip comp_{d}: sample rate {sr_c} != {sr}")
                    else:
                        if abs(c.shape[0] - ref_len) > max(1, int(ref_len * 0.02)):
                            print(
                                f"[backing] Warn comp_{d}: {c.shape[0] / sr:.3f}s "
                                f"vs drums {ref_len / sr:.3f}s (loop length mismatch)"
                            )
                        comp[d] = c
                        loaded_comp.append(d)

            if abs(stretch_rate - 1.0) >= 1e-3:
                print(f"[backing] Time-stretching kit {NATIVE_BPM:.0f} → {tempo:.0f} BPM (rate={stretch_rate:.4f})")
                count_in = _time_stretch(count_in, stretch_rate)
                drums = _time_stretch(drums, stretch_rate)
                bass = {d: _time_stretch(buf, stretch_rate) for d, buf in bass.items()}
                comp = {d: _time_stretch(buf, stretch_rate) for d, buf in comp.items()}
                ref_len = drums.shape[0]
            else:
                print(f"[backing] No stretch (native {NATIVE_BPM:.0f} BPM playback)")

        except Exception as exc:
            print(f"[backing] Failed to load stems: {exc}; MIDI fallback.")
            return False

        # Keep song clock on the same tempo we will play
        song.tempo_bpm = tempo

        prog = [int(x) for x in song.backing_degrees]
        missing = sorted({d for d in prog if d not in comp and d not in bass})
        print(
            f"[backing] Loaded kit from {self.assets_root} @ {tempo:.0f} BPM "
            f"sr={sr} (comp {loaded_comp or '—'}, bass {loaded_bass or '—'})"
        )
        if missing:
            print(f"[backing] Progression degrees with no stem (drums only): {missing}")

        # One bar duration in samples after any stretch
        samples_per_bar = max(1, int(round(ref_len)))

        with self._lock:
            self._sample_rate = int(sr)
            self._tempo_bpm = tempo
            self._samples_per_bar = samples_per_bar
            self._progression = prog
            self._count_in = count_in
            self._drums = drums
            self._bass = bass
            self._comp = comp
            self._playhead = 0
            self._running = False
            self._active = True

        self._ensure_stream()
        return True

    def _load_wav(self, path: Path) -> tuple[np.ndarray, int]:
        data, sr = sf.read(str(path), always_2d=True, dtype="float32")
        return _to_stereo_f32(data), int(sr)

    def _ensure_stream(self) -> None:
        if sd is None or not self._active:
            return
        if self._stream is not None:
            return
        self._stream = sd.OutputStream(
            samplerate=self._sample_rate,
            channels=2,
            dtype="float32",
            callback=self._callback,
            blocksize=512,
            latency="high",  # more stable than "low"; less underrun crackle
        )
        self._stream.start()

    def update(self, music_time: float, running: bool) -> None:
        """Publish transport. Playhead free-runs while playing; snap only on edges."""
        if not self._active:
            return
        with self._lock:
            target = music_time_to_samples(music_time, self._tempo_bpm, self._sample_rate)
            was_running = self._running
            snap_samples = int(SEEK_SNAP_SECONDS * self._sample_rate)

            if running and not was_running:
                # Start / resume from game position
                self._playhead = max(0, target)
            elif not running:
                # Pause: hold game position so resume is consistent
                self._playhead = max(0, target)
            elif abs(target - self._playhead) > snap_samples:
                # Large seek (stop/rewind/scrub)
                self._playhead = max(0, target)
            # else: leave playhead alone — callback advances it sample-accurately

            self._running = bool(running)

    def rewind(self) -> None:
        with self._lock:
            self._playhead = 0
            self._running = False

    def stop(self) -> None:
        with self._lock:
            self._running = False
            self._playhead = 0
            self._active = False
        stream = self._stream
        self._stream = None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    def shutdown(self) -> None:
        self.stop()

    def _callback(self, outdata, frames, time_info, status) -> None:  # noqa: ARG002
        with self._lock:
            running = self._running
            playhead = self._playhead
            sr = self._sample_rate
            spb = self._samples_per_bar
            progression = self._progression
            count_in = self._count_in
            drums = self._drums
            bass = self._bass
            comp = self._comp
            gain = self._gain
            active = self._active

            if active and running:
                self._playhead = playhead + frames

        outdata.fill(0.0)
        if not active or not running or count_in is None or drums is None:
            return

        if status:
            # Log underruns once in a while without spamming would be nicer; print is ok for now
            print(f"[backing] stream status: {status}")

        mix = np.zeros((frames, 2), dtype=np.float32)
        # Render in contiguous chunks so a bar boundary inside the block is clean
        remaining = frames
        local_pos = playhead
        out_off = 0
        while remaining > 0:
            bar = bar_index_from_samples(local_pos, spb)
            # Samples left in this bar
            if spb > 0:
                into_bar = local_pos % spb
                left_in_bar = spb - into_bar
            else:
                left_in_bar = remaining
            n = min(remaining, left_in_bar)

            if bar < 1:
                chunk = _read_loop(count_in, local_pos, n)
            else:
                chunk = _read_loop(drums, local_pos, n)
                deg = degree_for_bar(bar, progression)
                if deg is not None:
                    bbuf = bass.get(deg)
                    cbuf = comp.get(deg)
                    if bbuf is not None:
                        chunk = chunk + _read_loop(bbuf, local_pos, n)
                    if cbuf is not None:
                        chunk = chunk + _read_loop(cbuf, local_pos, n)

            mix[out_off : out_off + n] = chunk
            local_pos += n
            out_off += n
            remaining -= n

        mix *= gain
        np.clip(mix, -1.0, 1.0, out=mix)
        outdata[:] = mix
