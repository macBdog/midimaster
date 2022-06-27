import os
import pickle
from song import Song

class SongBook:
    """A song book is a persistent collecton of songs stored along with
    game options.
    """
    PATH = "ext/songs.pkl"

    def __init__(self):
        self.songs = {}
        self.input_device = ""
        self.output_device = ""


    def is_empty(self):
        return len(self.songs) == 0


    def get_default_song(self):
        song_key = next(iter(self.songs))
        return self.songs[song_key]


    def load(self):
        if os.path.exists(SongBook.PATH):
            with open(SongBook.PATH, 'rb') as book:
                self.songs = pickle.load(book)
                book.close()


    def save(self):
        with open(SongBook.PATH, 'wb') as book:
            pickle.dump(self.songs, book)
            book.close()


    def add_song(self, song:Song):
        self.songs[song.get_name()] = song
