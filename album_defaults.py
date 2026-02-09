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

    # Generate procedural venue albums for sight-reading challenges
    for tier in TIER_CONFIGS:
        album_name, songs = generate_venue_album(tier)
        album = songbook.add_album(album_name)
        for song in songs:
            album.add_update_song(song)

    album_name = "Real and Custom Songs"
    songbook.add_update_from_midi(Path("music/Nursery Rhyme - MaryHadALittleLamb.mid"), 1, album_name)

    songbook.validate()
    songbook.sort()

    return songbook
