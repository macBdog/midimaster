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

        def get_random_song(title:str, key: str) -> Song:
            s = Song()
            s.key_signature = key
            s.artist = f"Random"
            s.title = title
            s.path = ""
            s.ticks_per_beat = Song.SDQNotesPerBeat
            s.player_track_id = 0
            return s

        album = songbook.add_album("Play the Majors")
        s = get_random_song(title="C Workout", key="C")
        s.add_random_notes(num_notes=16, key=s.key_signature)
        album.add_update_song(s)

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
