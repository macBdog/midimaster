from album import Album
from song import Song
from song_book import SongBook
from pathlib import Path


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

    # Add/regenerate all the tutorial songs
    def get_random_song(title:str, key: str) -> Song:
        s = Song()
        s.key_signature = key
        s.artist = f"Tutorial"
        s.title = title
        s.path = ""
        s.ticks_per_beat = Song.SDQNotesPerBeat
        s.player_track_id = 0
        s.track_names = ["The Player", "Backing Track"]
        s.saved = False
        return s

    album = songbook.add_album("Play the Majors")
    s = get_random_song(title="C Workout", key="C")
    s.add_random_notes(num_notes=16, key=s.key_signature, tonic=60, note_length=8, note_spacing=8, time=32)
    album.add_update_song(s)

    album_name = "Real and Custom Songs"
    songbook.add_update_from_midi(Path("music/Nursery Rhyme - MaryHadALittleLamb.mid"), 1, album_name)

    songbook.validate()
    songbook.sort()

    return songbook
