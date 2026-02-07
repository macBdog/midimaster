import os
import pickle
from pathlib import Path

from song import Song
from album import Album

class SongBook:
    """A song book is a persistent, versionable collection of albums stored along with game options.
    """
    VERSION = 1
    PATH = "ext/songs.pkl"

    @staticmethod
    def load():
        if os.path.exists(SongBook.PATH):
            with open(SongBook.PATH, 'rb') as data_file:
                sb = pickle.load(data_file)
            return sb
        return None

    @staticmethod
    def save(book):
        with open(SongBook.PATH, 'wb') as data_file:
            pickle.dump(book, data_file)
            data_file.close()

    def __init__(self):
        self.validate()

    def __getstate__(self):
        if hasattr(self, "book_version"):
            return self.__dict__
        else:
            print(f"Song book must define book_version class variable!")

    def __setstate__(self, dict_):
        version_present_in_pickle = dict_.pop("book_version")
        if version_present_in_pickle != SongBook.VERSION:
            print(f"Error: Song book versions differ: latest is: {SongBook.VERSION}, in current book: {version_present_in_pickle}")
        else:
            self.__dict__ = dict_

    def validate(self):
        "Set any missing data that would occur as a result of a bad load or load from an outdated file."
        self.book_version = SongBook.VERSION
        if not hasattr(self, "albums"): self.albums: list[Album] = []
        if not hasattr(self, "default_song_title"): self.default_song_title = ""
        if not hasattr(self, "input_device"): self.input_device = ""
        if not hasattr(self, "output_device"): self.output_device = ""
        if not hasattr(self, "song_scores"): self.song_scores = ""
        if not hasattr(self, "show_note_names"): self.show_note_names = False
        if not hasattr(self, "output_latency_ms"): self.output_latency_ms = 0
        if not hasattr(self, "player_instrument"): self.player_instrument = 0  # Default to Acoustic Grand Piano

    def sort(self):
        sorted(self.albums, key=lambda album: album.get_max_score())

    def get_album_by_name(self, name: str) -> Album:
        for a in self.albums:
            if a.name == name:
                return a
        return None

    def get_num_albums(self):
        return len(self.albums)

    def is_empty(self):
        return len(self.albums) == 0

    def get_default_song(self) -> Song:
        for album in self.albums:
            song = album.find_song(title=self.default_song_title)
            if song is not None:
                return song
        if len(self.albums) > 0:
            self.albums[0].get_song[0]
        return None

    def find_song(self, title:str, artist:str) -> Song:
        """Return a song from any album where the title and artist matches."""
        for a in self.albums:
            return a.find_song(title, artist)

    def delete_album(self, album_id:int):
        del self.albums[album_id]

    def add_album(self, name:str) -> Album:
        """Albums are collections of songs that can be unlocked."""
        existing = self.get_album_by_name(name)
        if not existing:
            a = Album(name)
            self.albums.append(a)
            existing = a
        return existing

    def add_update_from_midi(self, midi_path: Path, track_id: int, album_name:str):
        album = self.get_album_by_name(album_name)
        if album is None:
            album = self.add_album(album_name)

        if midi_path.exists():
            new_song = Song()
            new_song.from_midi_file(midi_path, track_id)
            album.add_update_song(new_song)
