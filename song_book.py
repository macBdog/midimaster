import os
import pickle
from song import Song


class SongBook:
    """A song book is a persistent, versionable collecton of songs stored along with
    game options.
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


    def validate(self):
        "Set any missing data that would occur as a result of a bad load or load from an outdated file."
        self.book_version = SongBook.VERSION
        if not hasattr(self, "songs"): self.songs = []
        if not hasattr(self, "default_song"): self.default_song = 0
        if not hasattr(self, "input_device"): self.input_device = ""
        if not hasattr(self, "output_device"): self.output_device = ""
        if not hasattr(self, "song_scores"): self.song_scores = ""
        

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


    def get_song(self, id: int) -> Song:
        return self.songs[id]


    def get_num_songs(self):
        return len(self.songs)


    def is_empty(self):
        return len(self.songs) == 0


    def get_default_song(self):
        return self.songs[self.default_song]


    def add_song(self, song:Song):
        self.songs.append(song)


    def delete_song(self, song_id:int):
        self.songs.remove(self.songs[song_id])
