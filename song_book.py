import os
import pickle
from song import Song
from album import Album
from typing import List


class SongBook:
    """A song book is a persistent, versionable collecton of albums stored along with game options.
    """
    VERSION = 1
    PATH = "ext/songs.pkl"


    @staticmethod
    def load():
        if os.path.exists(SongBook.PATH):
            with open(SongBook.PATH, 'rb') as data_file:
                sb = pickle.load(data_file)
                data_file.close()
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
        if not hasattr(self, "albums"): self.albums:List[Album] = []
        if not hasattr(self, "default_song_title"): self.default_song_title = ""
        if not hasattr(self, "input_device"): self.input_device = ""
        if not hasattr(self, "output_device"): self.output_device = ""
        if not hasattr(self, "song_scores"): self.song_scores = ""


    def sort(self):
        sorted(self.albums, key=lambda album: album.get_max_score())


    def get_album(self, id: int) -> Song:
        return self.albums[id]


    def get_num_albums(self):
        return len(self.albums)


    def is_empty(self):
        return len(self.albums) == 0


    def get_default_song(self) -> Song:
        for album in self.albums:
            song = album.find_song(self.default_song_title)
            if song is not None:
                return song
        if len(self.albums) > 0:
            self.albums[0].get_song[0]
        return None


    def find_song(self, title:str, artist:str) -> Song:
        """Return a song from any album where the title and artist matches."""
        for a in self.albums:
            return a.find_song(title, artist)


    def add_update_song(self, song:Song):
        """Return True if a song with matching title and artist exists, saving the track ID."""
        for count, existing_song in enumerate(self.songs):
            if existing_song.artist.find(song.artist) >= 0 and existing_song.title.find(song.title) >= 0:
                song.player_track_id = self.songs[count].player_track_id
                self.songs[count] = song
                print(f"SongBook updated {song.get_name()}")
                return True

        self.songs.append(song)
        print(f"SongBook added {song.path} to data file.")
        return False


    def delete_album(self, album_id:int):
        self.albums.remove(self.songs[album_id])


    def add_album(self, name:str):
        """Albums are collections of songs that can be unlocked."""
        self.albums[name] = Album()


