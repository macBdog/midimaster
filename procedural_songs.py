"""Procedural song generation for sight-reading challenges.

Generates songs organized into difficulty-tiered albums (venues) that challenge
sight-reading ability while sounding musical through proper chord progressions
and melodic patterns.
"""

from enum import Enum, auto

import numpy.random as rng
from backing import (
    DEFAULT_ASSETS,
    NATIVE_BPM,
    choose_comp_instrument,
    discover_comp_instruments,
    harmonic_stems_present,
)
from note import Note
from song import Song


class ClefMode(Enum):
    """Staff clef used for notation display and melodic pitch limits.

    Only TREBLE is active today; BASS is reserved for future dual-staff support.
    """
    TREBLE = auto()
    BASS = auto()


# Inclusive MIDI note limits for pitches that render cleanly on each clef.
# Treble: low E (E3, ledger lines below the staff) through high F (F5, top line).
# Bass: placeholder (E2–middle C) until bass-clef rendering exists.
CLEF_PITCH_RANGE = {
    ClefMode.TREBLE: (52, 77),  # E3 .. F5
    ClefMode.BASS: (40, 60),    # E2 .. C4 (future)
}

# Career pitch ramp (MIDI). Starts around the G-clef, opens to the full staff
# plus ledger lines the treble renderer can show.
PITCH_START = (67, 71)  # G4 .. B4
PITCH_END = (52, 77)    # E3 .. F5

BAR_32NDS = 32
COUNT_IN_32NDS = 32
# Chance a bar includes a rest. assign_notes fills the resulting gap with rest glyphs.
REST_MOVING_CHANCE = 0.32
REST_WHOLE_BAR_CHANCE = 0.16

# Diatonic motifs as scale-degree offsets from a starting tone.
# Short shapes that stay singable when transposed onto a chord tone.
MOTIF_BANK = (
    (0,),
    (0, 0),
    (0, 2),
    (2, 0),
    (0, -1),
    (0, -1, 0),
    (0, 1, 2),
    (2, 1, 0),
    (0, 2, 4),
    (4, 2, 0),
    (0, 2, 4, 2),
    (0, 1, 2, 0),
    (0, 2, 1, 0),
    (0, 0, 1, 2),
    (2, 4, 2, 0),
    (0, 1, 0, -1),
)

# Game currently draws a single treble staff only.
DEFAULT_CLEF_MODE = ClefMode.TREBLE


def fit_pitch_to_range(pitch: int, lo: int, hi: int) -> int:
    """Shift pitch by octaves until it lies in [lo, hi] (inclusive)."""
    if lo > hi:
        return pitch
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    if pitch < lo:
        return max(lo, min(hi, pitch))
    return pitch


# Chord progressions library - intervals from root with chord types (MIDI fallback)
CHORD_PROGRESSIONS = {
    # Tiers 1-2: Simple pop triads
    "pop_basic": [(0, "major"), (5, "major"), (7, "major"), (0, "major")],  # I-IV-V-I
    "pop_vi": [(0, "major"), (5, "major"), (9, "minor"), (7, "major")],     # I-IV-vi-V
    "pop_axis": [(0, "major"), (7, "major"), (9, "minor"), (5, "major")],   # I-V-vi-IV
    "pop_50s": [(0, "major"), (9, "minor"), (5, "major"), (7, "major")],    # I-vi-IV-V
    "pop_minor_axis": [(9, "minor"), (5, "major"), (0, "major"), (7, "major")],  # vi-IV-I-V

    # Tier 3: Minor keys introduced
    "minor_classic": [(0, "minor"), (5, "minor"), (7, "major"), (0, "minor")],  # i-iv-V-i

    # Tiers 4-5: Jazz seventh chords
    "jazz_251": [(2, "min7"), (7, "dom7"), (0, "maj7")],                     # ii-V-I
    "jazz_turnaround": [(0, "maj7"), (9, "min7"), (2, "min7"), (7, "dom7")], # I-vi-ii-V
    "prog_36251": [
        (4, "minor"), (9, "minor"), (2, "min7"), (7, "dom7"), (0, "maj7")
    ],  # iii-vi-ii-V-I
}

# Scale-degree sequences for audio stem backing (assets/backing/)
DEGREE_PROGRESSIONS = {
    "145": [1, 4, 5, 1],
    "1564": [1, 5, 6, 4],
    "1645": [1, 6, 4, 5],
    "6415": [6, 4, 1, 5],
    "251": [2, 5, 1],
    "36251": [3, 6, 2, 5, 1],
}

# Display + preferred comp for career set titles (ASCII for the game font)
PROGRESSION_META = {
    "145": {"roman": "I-IV-V-I", "style": "Classic", "comp": "guitar"},
    "1564": {"roman": "I-V-vi-IV", "style": "Pop", "comp": "guitar"},
    "1645": {"roman": "I-vi-IV-V", "style": "Doo-wop", "comp": "guitar"},
    "6415": {"roman": "vi-IV-I-V", "style": "Minor pop", "comp": "ep"},
    "251": {"roman": "ii-V-I", "style": "Jazz", "comp": "ep"},
    "36251": {"roman": "iii-vi-ii-V-I", "style": "Turnaround", "comp": "ep"},
}

# Map didactic degree names → MIDI chord progression (fallback if stems missing)
DEGREE_TO_MIDI_PROG = {
    "145": "pop_basic",
    "1564": "pop_axis",
    "1645": "pop_50s",
    "6415": "pop_minor_axis",
    "251": "jazz_251",
    "36251": "prog_36251",
}

# Native stem tempo; generation clamps here so runtime stretch stays ~±10%
AUDIO_TEMPO_MIN = 90
AUDIO_TEMPO_MAX = 110

# Configuration for each difficulty tier (venue)
# degree_progressions: didactic stem sequences (see assets/backing/STEMS.md)
TIER_CONFIGS = {
    1: {
        "album_name": "Open Mic Night",
        "keys": ["C"],
        "tempo_range": (100, 100),
        "note_lengths": [32, 16],           # whole, half notes
        "note_range": 12,                   # 12 semitones, one octave
        "tonic_options": [48],              # middle C only
        "notes_per_song": (8, 16),
        "num_sets": 4,
        "progressions": ["pop_basic"],
        "degree_progressions": ["145", "1564", "1645", "6415"],
        "use_arpeggios": False,
    },
    2: {
        "album_name": "Coffee House Circuit",
        "keys": ["C"],
        "tempo_range": (90, 110),
        "note_lengths": [16, 8],            # half, quarter notes
        "note_range": 8,                    # octave
        "tonic_options": [60, 48],          # middle C, bass C
        "notes_per_song": (16, 24),
        "num_sets": 5,
        "progressions": ["pop_basic", "pop_vi"],
        "degree_progressions": ["145", "1564", "1645", "251", "6415"],
        "use_arpeggios": True,
    },
    3: {
        "album_name": "Club Tour",
        "keys": ["C"],
        "tempo_range": (90, 110),
        "note_lengths": [8, 4],             # quarter, eighth notes
        "note_range": 12,                   # 12 semitones
        "tonic_options": [48, 60, 72],
        "notes_per_song": (24, 40),
        "num_sets": 5,
        "progressions": ["jazz_251"],
        "degree_progressions": ["251", "36251", "1564", "1645", "6415"],
        "use_arpeggios": True,
    },
    4: {
        "album_name": "Festival Stage",
        "keys": ["C"],
        "tempo_range": (95, 110),
        "note_lengths": [8, 4, 2],          # quarter, eighth, 16th notes
        "note_range": 16,                   # wide range
        "tonic_options": [36, 48, 60, 72],
        "notes_per_song": (40, 64),
        "num_sets": 5,
        "progressions": ["jazz_251", "prog_36251"],
        "degree_progressions": ["251", "36251", "145", "1564", "6415"],
        "use_arpeggios": True,
    },
    5: {
        "album_name": "World Tour",
        "keys": ["C"],
        "tempo_range": (100, 110),
        "note_lengths": [4, 2, 1],          # eighth, 16th, 32nd notes
        "note_range": 24,                   # 2+ octaves
        "tonic_options": [36, 48, 60, 72, 84],
        "notes_per_song": (64, 96),
        "num_sets": 6,
        "progressions": ["jazz_251", "prog_36251"],
        "degree_progressions": ["145", "1564", "1645", "251", "36251", "6415"],
        "use_arpeggios": True,
    },
}

def career_set_index(tier: int, set_num: int) -> int:
    """0-based index of this set across the whole career."""
    prior = sum(TIER_CONFIGS[t]["num_sets"] for t in range(1, tier))
    return prior + set_num


def career_set_count() -> int:
    return sum(cfg["num_sets"] for cfg in TIER_CONFIGS.values())


def career_progress(tier: int, set_num: int) -> float:
    """0 at Open Mic set 1, 1 at the last World Tour set."""
    return career_set_index(tier, set_num) / max(career_set_count() - 1, 1)


def pitch_window(progress: float) -> tuple[int, int]:
    """Lerp the allowed MIDI range from the clef neighborhood to full staff."""
    p = max(0.0, min(1.0, progress))
    lo0, hi0 = PITCH_START
    lo1, hi1 = PITCH_END
    lo = int(round(lo0 + (lo1 - lo0) * p))
    hi = int(round(hi0 + (hi1 - hi0) * p))
    if hi - lo < 4:
        hi = lo + 4
    return lo, hi


def rhythm_profile(progress: float) -> tuple[list[int], int]:
    """Moving-note lengths and a longer resolve length (32nd units)."""
    if progress < 0.12:
        return [32], 32
    if progress < 0.28:
        return [32, 16], 32
    if progress < 0.44:
        return [16, 8], 16
    if progress < 0.60:
        return [16, 8], 16
    if progress < 0.76:
        return [8, 4], 16
    if progress < 0.90:
        return [8, 4, 2], 8
    return [4, 2], 8


def get_set_config(
    tier_config: dict,
    set_num: int,
    total_sets: int,
    progress: float | None = None,
) -> dict:
    """Scale difficulty from career-wide progress (falls back to in-venue)."""
    config = tier_config.copy()
    if progress is None:
        progress = set_num / max(total_sets - 1, 1)
    config["career_progress"] = float(progress)

    tempo_min, tempo_max = tier_config["tempo_range"]
    config["tempo"] = int(tempo_min + (tempo_max - tempo_min) * progress)

    notes_min, notes_max = tier_config["notes_per_song"]
    config["num_notes"] = int(notes_min + (notes_max - notes_min) * progress)

    moving, resolve = rhythm_profile(progress)
    config["moving_lengths"] = moving
    config["resolve_length"] = resolve
    config["note_lengths"] = list(dict.fromkeys(moving + [resolve]))
    config["pitch_lo"], config["pitch_hi"] = pitch_window(progress)
    return config

def progression_for_set(tier_config: dict, set_num: int) -> str:
    """Deterministic degree-progression id for a set (cycles if the list is short)."""
    progs = tier_config.get("degree_progressions") or []
    if not progs:
        return "145"
    return progs[set_num % len(progs)]


def format_set_title(set_num: int, degree_name: str, key: str) -> str:
    """Career song title. Keep 'Set N' prefix — song_book.score_key parses it.

    Album name is shown separately in the menu, so the title is the set only.
    """
    meta = PROGRESSION_META.get(degree_name, {})
    style = meta.get("style", degree_name)
    roman = meta.get("roman")
    body = f"{style} {roman}" if roman else style
    return f"Set {set_num + 1} in {key} - {body}"


def get_root_midi_for_key(key: str) -> int:
    """Get the MIDI note number for a key's root in the bass register.
    Args:
        key: Key signature string (e.g., "C", "Gm", "F#")
    Returns:
        MIDI note number for the root (in octave 3, around 48-59)
    """
    # Remove minor indicator to get root note name
    root_name = key.replace("m", "")

    # Base MIDI values for each note in octave 3
    note_to_midi = {
        'C': 48, 'D': 50, 'E': 52, 'F': 53, 'G': 55, 'A': 57, 'B': 59
    }

    root_midi = note_to_midi.get(root_name[0], 48)

    # Adjust for sharps/flats
    if len(root_name) > 1:
        if root_name[1] == '#':
            root_midi += 1
        elif root_name[1] == 'b':
            root_midi -= 1

    return root_midi


def scale_pitch_classes(key: str) -> list[int]:
    """Seven pitch classes of a major or natural-minor key, tonic first."""
    is_major = key.find("m") < 0
    tonic_name = key.replace("m", "")
    note_to_pc = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    root = note_to_pc.get(tonic_name[0], 0)
    if len(tonic_name) > 1:
        if tonic_name[1] == "#":
            root = (root + 1) % 12
        elif tonic_name[1] == "b":
            root = (root - 1) % 12
    steps = [0, 2, 4, 5, 7, 9, 11] if is_major else [0, 2, 3, 5, 7, 8, 10]
    return [(root + s) % 12 for s in steps]


def chord_tone_degrees(roman_degree: int) -> tuple[int, int, int]:
    """Scale degrees (0–6) for the triad on a 1–6 Roman numeral."""
    root = (int(roman_degree) - 1) % 7
    return root, (root + 2) % 7, (root + 4) % 7


def nearest_degree(target: int, choices: tuple[int, ...] | list[int]) -> int:
    best = choices[0]
    best_d = 8
    for c in choices:
        d = min((target - c) % 7, (c - target) % 7)
        if d < best_d:
            best, best_d = c, d
    return best


def pitches_for_degrees(
    degrees: tuple[int, ...] | list[int],
    lo: int,
    hi: int,
    scale_pcs: list[int],
) -> list[int]:
    pcs = {scale_pcs[d % 7] for d in degrees}
    return [p for p in range(lo, hi + 1) if p % 12 in pcs]


def pitch_for_degree(
    degree: int,
    prev: int | None,
    lo: int,
    hi: int,
    scale_pcs: list[int],
) -> int:
    pool = pitches_for_degrees((degree,), lo, hi, scale_pcs)
    if not pool:
        pool = [p for p in range(lo, hi + 1) if (p % 12) in scale_pcs]
    if not pool:
        pool = [max(lo, min(hi, 67))]
    if prev is None:
        return pool[len(pool) // 2]
    return min(pool, key=lambda p: (abs(p - prev), abs(p - 67)))


def resolve_pitch(
    chord: tuple[int, int, int],
    prev: int | None,
    lo: int,
    hi: int,
    scale_pcs: list[int],
    cadence: bool,
) -> int:
    pool = pitches_for_degrees(chord, lo, hi, scale_pcs)
    if cadence:
        roots = [p for p in pool if p % 12 == scale_pcs[chord[0]]]
        if roots:
            pool = roots
    if not pool:
        return pitch_for_degree(chord[0], prev, lo, hi, scale_pcs)
    if prev is None:
        return pool[len(pool) // 2]
    return min(pool, key=lambda p: (abs(p - prev), abs(p - 67)))


def _pick_rest_slot(
    n: int,
    first_bar: bool,
    last_bar: bool,
    cadence: bool,
    after_rest: bool,
) -> int | None:
    """Index of a duration to skip, or None. Never the bar-ending chord tone."""
    if n <= 0:
        return None
    if n == 1:
        if first_bar or last_bar or cadence or after_rest:
            return None
        return 0 if rng.random() < REST_WHOLE_BAR_CHANCE else None
    if rng.random() >= REST_MOVING_CHANCE:
        return None
    slots = list(range(n - 1))
    if first_bar:
        slots = [s for s in slots if s != 0]
    if not slots:
        return None
    return int(rng.choice(slots))


def pick_motif(num_notes: int, prefer: tuple[int, ...] | None) -> tuple[int, ...]:
    if prefer is not None and 1 <= len(prefer) <= num_notes:
        return prefer
    fit = [m for m in MOTIF_BANK if 1 <= len(m) <= num_notes]
    if not fit:
        return (0,)
    return fit[int(rng.randint(0, len(fit)))]


def bar_durations(moving: list[int], resolve: int, cadence: bool) -> list[int]:
    """Durations that fill one bar. Last value is the held chord-tone."""
    hold = max(resolve, 16) if cadence else resolve
    hold = min(BAR_32NDS, max(hold, 1))
    if hold >= BAR_32NDS:
        return [BAR_32NDS]
    remaining = BAR_32NDS - hold
    parts: list[int] = []
    while remaining > 0:
        choices = [d for d in moving if d <= remaining]
        if not choices:
            choices = [d for d in (16, 8, 4, 2, 1) if d <= remaining]
        if not parts and 2 in moving and 2 <= remaining:
            parts.append(2)
        else:
            parts.append(int(rng.choice(choices)))
        remaining -= parts[-1]
    parts.append(hold)
    return parts


def add_backing_progression(song: Song, progression_name: str, start_time: int = 32):
    """Add backing chords following a musical progression.
    Args:
        song: Song to add backing track to
        progression_name: Name of progression from CHORD_PROGRESSIONS
        start_time: When to start the backing (in 32nd notes)
    """
    progression = CHORD_PROGRESSIONS.get(progression_name, CHORD_PROGRESSIONS["pop_basic"])
    root_midi = get_root_midi_for_key(song.key_signature)

    # Calculate song duration
    if song.notes:
        song_end = song.notes[-1].time + song.notes[-1].length
    else:
        song_end = 128  # Default 4 bars

    # Chord duration: 1 bar = 32 thirty-second notes
    chord_duration = 32
    num_chords_needed = max(1, (song_end - start_time) // chord_duration + 1)

    chord_index = 0
    is_first = True

    for i in range(num_chords_needed):
        interval, chord_type = progression[chord_index % len(progression)]
        chord_root = root_midi + interval

        song.add_backing_chord(
            root=chord_root,
            chord_type=chord_type,
            duration=chord_duration,
            track_id=1,
            time=start_time if is_first else 0,
            velocity=70
        )

        is_first = False
        chord_index += 1

def generate_melodic_content(
    song: Song,
    config: dict,
    degree_name: str,
    clef_mode: ClefMode | None = DEFAULT_CLEF_MODE,
):
    """Write a bar-aligned melody over the stem progression.

    Each bar ends on a chord tone, held longer than the moving notes.
    Motifs are reused (transposed onto the new chord) so phrases feel thematic.
    Occasional gaps become rests when notes are assigned for drawing.
    """
    degrees = DEGREE_PROGRESSIONS.get(degree_name, DEGREE_PROGRESSIONS["145"])
    scale_pcs = scale_pitch_classes(song.key_signature)
    lo = int(config.get("pitch_lo", PITCH_START[0]))
    hi = int(config.get("pitch_hi", PITCH_START[1]))
    if clef_mode is not None:
        c_lo, c_hi = CLEF_PITCH_RANGE[clef_mode]
        lo, hi = max(lo, c_lo), min(hi, c_hi)
    moving = list(config.get("moving_lengths") or [32])
    resolve = int(config.get("resolve_length") or 32)
    cycles = 2 + int(float(config.get("career_progress", 0.0)) * 2)
    bars = len(degrees) * max(2, cycles)

    time_32 = COUNT_IN_32NDS
    prev_pitch: int | None = None
    last_motif: tuple[int, ...] | None = None
    after_rest = False

    for bar_i in range(bars):
        roman = degrees[bar_i % len(degrees)]
        chord = chord_tone_degrees(roman)
        cadence = (bar_i + 1) % len(degrees) == 0
        durs = bar_durations(moving, resolve, cadence)
        n = len(durs)
        first_bar = bar_i == 0
        last_bar = bar_i == bars - 1
        rest_i = _pick_rest_slot(n, first_bar, last_bar, cadence, after_rest)

        if rest_i == 0 and n == 1:
            time_32 += durs[0]
            after_rest = True
            continue

        reuse = last_motif is not None and rng.random() < 0.55
        motif = pick_motif(n, last_motif if reuse else None)
        last_motif = motif
        start = int(rng.choice(chord))

        after_rest = False
        for i, length in enumerate(durs):
            if i == rest_i:
                time_32 += length
                after_rest = True
                continue
            if i == n - 1:
                pitch = resolve_pitch(chord, prev_pitch, lo, hi, scale_pcs, cadence)
            else:
                step_deg = (start + motif[i % len(motif)]) % 7
                pitch = pitch_for_degree(step_deg, prev_pitch, lo, hi, scale_pcs)
            song.notes.append(Note(int(pitch), int(time_32), int(length)))
            prev_pitch = pitch
            time_32 += length
            after_rest = False

def generate_procedural_song(
    config: dict,
    title: str,
    artist: str,
    clef_mode: ClefMode | None = DEFAULT_CLEF_MODE,
    degree_name: str | None = None,
    song: Song | None = None,
) -> Song:
    """Generate a single procedural song from configuration.

    Pass an existing ``song`` to reset it in place (score is kept).
    """
    if song is None:
        song = Song()
    song.artist = artist
    song.title = title
    song.key_signature = rng.choice(config["keys"]).item()
    song.tempo_bpm = config["tempo"]
    song.ticks_per_beat = Song.SDQNotesPerBeat
    song.track_names = ["Player", "Backing"]
    song.saved = False
    song.notes = []
    song.backing_tracks = {}
    song.backing_degrees = []
    song.use_audio_backing = False
    song.backing_comp = None

    degree_names = config.get("degree_progressions")
    if degree_name is None and degree_names:
        degree_name = rng.choice(degree_names).item()
    if degree_name is None:
        degree_name = "145"

    generate_melodic_content(song, config, degree_name, clef_mode=clef_mode)

    song.backing_degrees = list(DEGREE_PROGRESSIONS[degree_name])
    song.use_audio_backing = harmonic_stems_present(DEFAULT_ASSETS, song.key_signature)
    if song.use_audio_backing:
        song.tempo_bpm = int(NATIVE_BPM)
        preferred = PROGRESSION_META.get(degree_name, {}).get("comp")
        instruments = discover_comp_instruments(DEFAULT_ASSETS, song.key_signature)
        song.backing_comp = choose_comp_instrument(instruments, preferred)
    midi_prog = DEGREE_TO_MIDI_PROG.get(degree_name, "pop_basic")
    add_backing_progression(song, midi_prog, start_time=COUNT_IN_32NDS)

    return song

def generate_venue_album(tier: int) -> tuple[str, list[Song]]:
    """Generate all songs for a venue album.
    Args:
        tier: Difficulty tier (1-5)
    Returns:
        Tuple of (album_name, list of songs)
    """
    tier_config = TIER_CONFIGS[tier]
    album_name = tier_config["album_name"]
    num_sets = tier_config["num_sets"]
    songs = []

    for set_num in range(num_sets):
        set_config = get_set_config(
            tier_config, set_num, num_sets, progress=career_progress(tier, set_num)
        )
        deg_name = progression_for_set(tier_config, set_num)
        song = generate_procedural_song(
            set_config, "", album_name, degree_name=deg_name
        )
        song.title = format_set_title(set_num, deg_name, song.key_signature)
        songs.append(song)

    return album_name, songs

def get_tier_for_album(album_name: str) -> int | None:
    """Get the tier number for a venue album name.
    Args:
        album_name: Name of the album
    Returns:
        Tier number (1-5) if this is a venue album, None otherwise
    """
    for tier, config in TIER_CONFIGS.items():
        if config["album_name"] == album_name:
            return tier
    return None

def is_venue_album(album_name: str) -> bool:
    """Check if an album is a procedural venue album.
    Args:
        album_name: Name of the album
    Returns:
        True if this is a venue album
    """
    return get_tier_for_album(album_name) is not None

def regenerate_set(tier: int, set_num: int, song: Song | None = None) -> Song:
    """Rebuild a set with fresh random content.

    Pass ``song`` to reset that object in place so menu widgets keep their
    reference. Score on a reused song is left intact.
    """
    tier_config = TIER_CONFIGS[tier]
    album_name = tier_config["album_name"]
    num_sets = tier_config["num_sets"]

    set_config = get_set_config(
        tier_config, set_num, num_sets, progress=career_progress(tier, set_num)
    )
    deg_name = progression_for_set(tier_config, set_num)
    song = generate_procedural_song(
        set_config, "", album_name, degree_name=deg_name, song=song
    )
    song.title = format_set_title(set_num, deg_name, song.key_signature)
    return song
