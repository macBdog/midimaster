from album import Album
from song import Song
from song_book import SongBook
from pathlib import Path


def setup_songbook_albums() -> SongBook:
    # Read the songbook and load the first song
    songbook = SongBook.load()

    if songbook is None:
        songbook = SongBook()

        album_name = "The Basics"
        songbook.add_update_from_midi(Path("music/CMajor.mid"), 1, album_name)
        songbook.add_update_from_midi(Path("music/CMinor.mid"), 1, album_name)
        songbook.add_update_from_midi(Path("music/Nursery Rhyme - MaryHadALittleLamb.mid"), 1, album_name)

        def add_random_song_to_album(album: Album, **kwargs):
            s = Song()
            s.from_random(**kwargs)
            album.add_update_song(s)

        album = songbook.add_album("Whole Note Majors/Minors 1-4-5")
        add_random_song_to_album(album, key="C")
        add_random_song_to_album(album, key="F")
        add_random_song_to_album(album, key="G")
        add_random_song_to_album(album, key="Em")
        add_random_song_to_album(album, key="Am")
        add_random_song_to_album(album, key="Bm")

        album = songbook.add_album("Half Note Majors/Minors 2-5-1")
        add_random_song_to_album(album, key="D", note_len_range=(16,16), note_spacing_range=(16,16))
        add_random_song_to_album(album, key="G", note_len_range=(16,16), note_spacing_range=(16,16))
        add_random_song_to_album(album, key="C", note_len_range=(16,16), note_spacing_range=(16,16))
        add_random_song_to_album(album, key="Fm", note_len_range=(16,16), note_spacing_range=(16,16))
        add_random_song_to_album(album, key="Bm", note_len_range=(16,16), note_spacing_range=(16,16))
        add_random_song_to_album(album, key="Em", note_len_range=(16,16), note_spacing_range=(16,16))

        album_name = "Real and Custom Songs"
        songbook.add_update_from_midi(Path("music/Duke Ellington - Take the A Train.mid"), 1, album_name)
        songbook.add_update_from_midi(Path("music/Eden Ahbez - Nature Boy.mid"), 1, album_name)

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
    songbook.sort()

    return songbook
