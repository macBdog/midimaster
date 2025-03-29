from song import Song

class Album():
    """Albums are groups of songs that can be unlocked."""
    DefaultName = "Custom"
    def __init__(self, name = DefaultName):
        self.name = name
        self.songs: list[Song] = []
        self.expanded = False


    def get_max_score(self) -> int:
        score = 0
        for s in self.songs:
            score += s.get_max_score()
        return score


    def sort(self):
        sorted(self.songs, key=lambda s: s.get_max_score())


    def get_song(self, id: int) -> Song:
        return self.songs[id]


    def get_num_songs(self):
        return len(self.songs)


    def find_song(self, title:str, artist:str = "") -> Song:
        """Return a song where the title and artist matches."""
        for song in self.songs:
            if song.artist.find(artist) >= 0 or song.title.find(title) >= 0:
                return song


    def add_song(self, title:str, artist:str):
        if song := self.find_song(title=title, artist=artist):
            self.songs.append(song)


    def add_song(self, song:Song):
        self.songs.append(song)


    def add_update_song(self, song:Song) -> bool:
        """Return True if a song with matching title and artist exists, saving the track ID."""
        for count, existing_song in enumerate(self.songs):
            if existing_song.artist.find(song.artist) >= 0 and existing_song.title.find(song.title) >= 0:
                song.player_track_id = self.songs[count].player_track_id
                self.songs[count] = song
                print(f"Album updated with {song.get_name()}")
                return True

        self.songs.append(song)
        return False


    def delete_song(self, song_id:int):
        self.songs.remove(self.songs[song_id])
