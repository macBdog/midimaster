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
    def get_random_song(title:str, key: str, tempo: int = 100) -> Song:
        s = Song()
        s.key_signature = key
        s.artist = f"Tutorial"
        s.title = title
        s.path = ""
        s.ticks_per_beat = Song.SDQNotesPerBeat
        s.player_track_id = 0
        s.track_names = ["The Player", "Backing Track"]
        s.saved = False
        s.tempo_bpm = tempo
        return s

    album = songbook.add_album("Play the Majors")
    s = get_random_song(title="C Workout", key="C", tempo=80)
    s.add_random_notes(num_notes=1, key=s.key_signature, tonic=60, note_length=32, time=32)
    s.add_random_notes(num_notes=4, key=s.key_signature, tonic=60, note_length=16)
    s.add_random_notes(num_notes=16, key=s.key_signature, tonic=60, note_length=8)
    s.add_random_notes(num_notes=32, key=s.key_signature, tonic=60, note_length=4)
    album.add_update_song(s)

    album_name = "Real and Custom Songs"
    songbook.add_update_from_midi(Path("music/Nursery Rhyme - MaryHadALittleLamb.mid"), 1, album_name)

    songbook.validate()
    songbook.sort()

    return songbook
