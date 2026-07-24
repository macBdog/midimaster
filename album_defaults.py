from album import Album
from song import Song
from song_book import SongBook
from pathlib import Path
from procedural_songs import generate_venue_album, TIER_CONFIGS


def setup_songbook_albums() -> SongBook:
    # Read the songbook and load the custom songs
    songbook = SongBook.load()
    if songbook is None:
        songbook = SongBook()
    else:
        # Patch up older versions on songbooks without albums
        if type(getattr(songbook, "albums")) == dict:
            songbook.albums = []

        if songbook.get_num_albums() == 0 and getattr(songbook, "songs"):
            album = songbook.add_album(Album.DefaultName)
            for s in songbook.songs:
                album.add_update_song(s)
            del songbook.songs

    songbook.validate()

    # Venue XP is career-scoped. Stale venue:* scores were re-applied on every
    # boot even with no active career, so Set 1 showed e.g. 80/80 XP unplayed.
    career_active = bool(getattr(songbook.career, "active", False))
    if not career_active:
        had_venue_scores = any(str(k).startswith("venue:") for k in songbook.song_scores)
        songbook.song_scores = {
            key: value
            for key, value in songbook.song_scores.items()
            if not str(key).startswith("venue:")
        }
        if had_venue_scores:
            SongBook.save(songbook)

    # Generate procedural venue albums for sight-reading challenges.
    # Fresh Song objects each boot — re-apply bests only during an active run.
    for tier in TIER_CONFIGS:
        album_name, songs = generate_venue_album(tier)
        album = songbook.add_album(album_name)
        for set_index, song in enumerate(songs):
            if career_active:
                songbook.apply_stored_score(song, venue_tier=tier, set_index=set_index)
            album.add_update_song(song)

    album_name = "Real and Custom Songs"
    songbook.add_update_from_midi(Path("music/Nursery Rhyme - MaryHadALittleLamb.mid"), 1, album_name)

    songbook.sort()

    return songbook
