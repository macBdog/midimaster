"""Procedural song generation for sight-reading challenges.

Generates songs organized into difficulty-tiered albums (venues) that challenge
sight-reading ability while sounding musical through proper chord progressions
and melodic patterns.
"""

import numpy.random as rng
from song import Song

# Chord progressions library - intervals from root with chord types
CHORD_PROGRESSIONS = {
    # Tiers 1-2: Simple pop triads
    "pop_basic": [(0, "major"), (5, "major"), (7, "major"), (0, "major")],  # I-IV-V-I
    "pop_vi": [(0, "major"), (5, "major"), (9, "minor"), (7, "major")],     # I-IV-vi-V

    # Tier 3: Minor keys introduced
    "minor_classic": [(0, "minor"), (5, "minor"), (7, "major"), (0, "minor")],  # i-iv-V-i

    # Tiers 4-5: Jazz seventh chords
    "jazz_251": [(2, "min7"), (7, "dom7"), (0, "maj7")],                     # ii-V-I
    "jazz_turnaround": [(0, "maj7"), (9, "min7"), (2, "min7"), (7, "dom7")], # I-vi-ii-V
}

# Configuration for each difficulty tier (venue)
TIER_CONFIGS = {
    1: {
        "album_name": "Open Mic Night",
        "keys": ["C"],
        "tempo_range": (60, 70),
        "note_lengths": [32, 16],           # whole, half notes
        "note_range": 5,                    # 5 semitones
        "tonic_options": [60],              # middle C only
        "notes_per_song": (8, 16),
        "num_sets": 4,
        "progressions": ["pop_basic"],
        "use_arpeggios": False,
    },
    2: {
        "album_name": "Coffee House Circuit",
        "keys": ["C", "G", "F"],
        "tempo_range": (70, 85),
        "note_lengths": [16, 8],            # half, quarter notes
        "note_range": 8,                    # octave
        "tonic_options": [60, 48],          # middle C, bass C
        "notes_per_song": (16, 24),
        "num_sets": 5,
        "progressions": ["pop_basic", "pop_vi"],
        "use_arpeggios": True,
    },
    3: {
        "album_name": "Club Tour",
        "keys": ["C", "G", "D", "F", "Bb", "Am", "Em", "Dm"],
        "tempo_range": (80, 100),
        "note_lengths": [8, 4],             # quarter, eighth notes
        "note_range": 12,                   # 12 semitones
        "tonic_options": [48, 60, 72],
        "notes_per_song": (24, 40),
        "num_sets": 5,
        "progressions": ["pop_basic", "pop_vi", "minor_classic"],
        "use_arpeggios": True,
    },
    4: {
        "album_name": "Festival Stage",
        "keys": ["C", "G", "D", "A", "E", "B", "F", "Bb", "Eb", "Ab",
                 "Am", "Em", "Bm", "Dm", "Gm", "Cm"],
        "tempo_range": (95, 120),
        "note_lengths": [8, 4, 2],          # quarter, eighth, 16th notes
        "note_range": 16,                   # wide range
        "tonic_options": [36, 48, 60, 72],
        "notes_per_song": (40, 64),
        "num_sets": 5,
        "progressions": ["pop_vi", "minor_classic", "jazz_251"],
        "use_arpeggios": True,
    },
    5: {
        "album_name": "World Tour",
        "keys": ["C", "G", "D", "A", "E", "B", "F#", "C#",
                 "F", "Bb", "Eb", "Ab", "Db", "Gb",
                 "Am", "Em", "Bm", "F#m", "C#m", "Dm", "Gm", "Cm", "Fm"],
        "tempo_range": (110, 140),
        "note_lengths": [4, 2, 1],          # eighth, 16th, 32nd notes
        "note_range": 24,                   # 2+ octaves
        "tonic_options": [36, 48, 60, 72, 84],
        "notes_per_song": (64, 96),
        "num_sets": 6,
        "progressions": ["jazz_251", "jazz_turnaround"],
        "use_arpeggios": True,
    },
}

def get_set_config(tier_config: dict, set_num: int, total_sets: int) -> dict:
    """Scale difficulty based on set number within the tier.
    Args:
        tier_config: Base configuration for the tier
        set_num: Current set number (0-indexed)
        total_sets: Total number of sets in the album
    Returns:
        Modified configuration for this specific set
    """
    config = tier_config.copy()
    progress = set_num / max(total_sets - 1, 1)  # 0.0 to 1.0

    # Scale tempo based on progress
    tempo_min, tempo_max = tier_config["tempo_range"]
    config["tempo"] = int(tempo_min + (tempo_max - tempo_min) * progress)

    # Scale note count based on progress
    notes_min, notes_max = tier_config["notes_per_song"]
    config["num_notes"] = int(notes_min + (notes_max - notes_min) * progress)

    # Later sets use shorter note values (remove longest options)
    if progress > 0.6 and len(tier_config["note_lengths"]) > 1:
        config["note_lengths"] = tier_config["note_lengths"][1:]

    return config

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

def generate_melodic_content(song: Song, config: dict, tonic: int, total_notes: int):
    """Generate melodic content using a mix of random notes and arpeggios.
    Args:
        song: Song to add notes to
        config: Configuration dict with generation parameters
        tonic: MIDI note number for the tonal center
        total_notes: Total number of notes to generate
    """
    notes_remaining = total_notes
    phrase_length = min(8, max(4, total_notes // 4))
    use_arpeggios = config.get("use_arpeggios", False)
    is_first_phrase = True

    while notes_remaining > 0:
        notes_in_phrase = min(phrase_length, notes_remaining)
        note_length = rng.choice(config["note_lengths"]).item()

        # Alternate between random notes and arpeggios for variety
        use_arpeggio_now = use_arpeggios and notes_remaining < total_notes // 2 and notes_in_phrase >= 4

        if use_arpeggio_now:
            # Use arpeggio for musical interest
            pattern = rng.choice(["up", "down", "up-down"]).item()
            song.add_arpeggio(
                num_notes=notes_in_phrase,
                key=song.key_signature,
                tonic=tonic,
                pattern=pattern,
                note_length=note_length,
                time=32 if is_first_phrase else 0  # Start after 1 bar lead-in
            )
        else:
            # Use random notes within the key
            song.add_random_notes(
                num_notes=notes_in_phrase,
                key=song.key_signature,
                tonic=tonic,
                note_range=config["note_range"],
                note_length=note_length,
                time=32 if is_first_phrase else 0  # Start after 1 bar lead-in
            )

        is_first_phrase = False
        notes_remaining -= notes_in_phrase

        # Occasionally shift tonic for variety (if multiple options available)
        if notes_remaining > phrase_length and len(config["tonic_options"]) > 1:
            if rng.random() > 0.7:
                tonic = rng.choice(config["tonic_options"]).item()

def generate_procedural_song(config: dict, title: str, artist: str) -> Song:
    """Generate a single procedural song from configuration.
    Args:
        config: Configuration dict with all generation parameters
        title: Song title
        artist: Artist/album name
    Returns:
        Generated Song object
    """
    song = Song()
    song.artist = artist
    song.title = title
    song.key_signature = rng.choice(config["keys"]).item()
    song.tempo_bpm = config["tempo"]
    song.ticks_per_beat = Song.SDQNotesPerBeat
    song.track_names = ["Player", "Backing"]
    song.saved = False

    # Generate melodic content
    tonic = rng.choice(config["tonic_options"]).item()
    generate_melodic_content(song, config, tonic, config["num_notes"])

    # Add backing track
    progression = rng.choice(config["progressions"]).item()
    add_backing_progression(song, progression, start_time=32)

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
        set_config = get_set_config(tier_config, set_num, num_sets)

        # Generate title with key (will be set after song is created)
        song = generate_procedural_song(set_config, f"Set {set_num + 1}", album_name)

        # Update title to include key
        song.title = f"Set {set_num + 1} in {song.key_signature}"

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

def regenerate_set(tier: int, set_num: int) -> "Song":
    """Regenerate a single set with fresh random content.
    Called when a player bombs a set and needs to retry.
    Args:
        tier: Venue tier (1-5)
        set_num: Set index within venue (0-indexed)
    Returns:
        Newly generated Song object
    """
    tier_config = TIER_CONFIGS[tier]
    album_name = tier_config["album_name"]
    num_sets = tier_config["num_sets"]

    set_config = get_set_config(tier_config, set_num, num_sets)
    song = generate_procedural_song(set_config, f"Set {set_num + 1}", album_name)
    song.title = f"Set {set_num + 1} in {song.key_signature}"

    return song
