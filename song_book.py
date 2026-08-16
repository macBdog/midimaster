import os
import pickle
import re
import shutil
from pathlib import Path

from song import Song
from album import Album
from career import Career

# On-disk MIDI imports are copied here so paths stay stable across sessions.
MUSIC_DIR = Path("music")

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
        if not hasattr(self, "book_version"):
            print(f"Song book must define book_version class variable!")
            return None

        # Create a copy of the state, filtering out unsaved songs
        state = self.__dict__.copy()

        # Filter albums to only include those with saved songs
        filtered_albums = []
        for album in self.albums:
            # Filter songs to only include saved ones
            saved_songs = [song for song in album.songs if song.saved]
            if saved_songs:
                # Create a copy of the album with only saved songs
                filtered_album = Album(album.name)
                filtered_album.songs = saved_songs
                filtered_album.expanded = album.expanded
                filtered_albums.append(filtered_album)

        state["albums"] = filtered_albums
        # song_scores is kept in state (venue songs are not pickled; scores live here)
        return state

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
        if not hasattr(self, "song_scores") or not isinstance(getattr(self, "song_scores", None), dict):
            self.song_scores = {}
        if not hasattr(self, "show_note_names"): self.show_note_names = False
        if not hasattr(self, "output_latency_ms"): self.output_latency_ms = 0
        if not hasattr(self, "player_instrument"): self.player_instrument = 0  # Default to Acoustic Grand Piano
        if not hasattr(self, "backing_comp"): self.backing_comp = "auto"
        if not hasattr(self, "career"): self.career = Career()

    @staticmethod
    def score_key(song: Song, venue_tier: int | None = None, set_index: int | None = None) -> str:
        """Stable key for best-score storage (venue sets outlive regenerated Song objects)."""
        from procedural_songs import get_tier_for_album

        tier = venue_tier if venue_tier is not None else get_tier_for_album(song.artist)
        if tier is None:
            # Prefer path for on-disk midi; fall back to display name
            if song.path:
                return f"song:{song.path}"
            return f"song:{song.get_name()}"

        if set_index is None:
            match = re.match(r"Set (\d+)", song.title or "")
            set_index = int(match.group(1)) - 1 if match else 0
        return f"venue:{tier}:{set_index}"

    @staticmethod
    def _is_practice_mode(mode) -> bool:
        """Pause & Learn is practice-only and must not affect career XP."""
        return getattr(mode, "name", None) == "PAUSE_AND_LEARN"

    def get_best_score(
        self, song: Song, venue_tier: int | None = None, set_index: int | None = None
    ) -> float:
        """Best career/performance score from the song object and song_scores.

        Pause & Learn scores are excluded — practice runs do not count toward XP.
        """
        best = 0.0
        if song.score:
            for key, value in song.score.items():
                if self._is_practice_mode(key):
                    continue
                try:
                    best = max(best, float(value))
                except (TypeError, ValueError):
                    pass
        score_key = self.score_key(song, venue_tier, set_index)
        best = max(best, float(self.song_scores.get(score_key, 0) or 0))
        return best

    def record_score(
        self,
        song: Song,
        score: float,
        venue_tier: int | None = None,
        set_index: int | None = None,
        mode=None,
    ) -> float:
        """Keep the best score on the song and in persistent song_scores. Returns best.

        Venue set XP is only written to song_scores during an active career so
        free-play / inactive runs do not leave stale bests on the next boot.
        Pause & Learn (practice) updates only song.score[mode], never career XP.
        """
        score = float(score)
        if mode is not None:
            existing = song.score.get(mode, 0) if mode in song.score else 0
            song.score[mode] = max(score, existing)

        if self._is_practice_mode(mode):
            return score

        key = self.score_key(song, venue_tier, set_index)
        best = max(score, float(self.song_scores.get(key, 0) or 0))
        if song.score:
            for score_key, value in song.score.items():
                if self._is_practice_mode(score_key):
                    continue
                try:
                    best = max(best, float(value))
                except (TypeError, ValueError):
                    pass

        is_venue = str(key).startswith("venue:")
        if is_venue and not getattr(self.career, "active", False):
            return best

        self.song_scores[key] = best
        return best

    def apply_stored_score(
        self, song: Song, venue_tier: int | None = None, set_index: int | None = None, mode=None
    ):
        """Copy persistent best score onto a newly generated song for menu display."""
        key = self.score_key(song, venue_tier, set_index)
        best = float(self.song_scores.get(key, 0) or 0)
        if best <= 0:
            return
        if mode is not None:
            song.score[mode] = max(best, song.score.get(mode, 0) if mode in song.score else 0)
        else:
            # Mode-agnostic stash so get_best_score still sees it if score dict is empty of enums
            song.score["_best"] = max(best, float(song.score.get("_best", 0) or 0))

    def clear_venue_scores(self):
        """Reset all career/venue set XP (for a new or abandoned career run)."""
        from procedural_songs import get_tier_for_album

        self.song_scores = {
            key: value
            for key, value in self.song_scores.items()
            if not str(key).startswith("venue:")
        }
        for album in self.albums:
            if get_tier_for_album(album.name) is None:
                continue
            for song in album.songs:
                song.score = {}

    def sort(self):
        sorted(self.albums, key=lambda album: album.get_max_score())

    def get_num_songs(self):
        num_songs = 0
        for album in self.albums:
            num_songs += album.get_num_songs()
        return num_songs

    def get_album_by_name(self, name: str) -> Album | None:
        for a in self.albums:
            if a.name == name:
                return a
        return None

    def get_num_albums(self) -> int:
        return len(self.albums)

    def is_empty(self):
        return len(self.albums) == 0

    def get_default_song(self) -> Song | None:
        for album in self.albums:
            song = album.find_song(title=self.default_song_title)
            if song is not None:
                return song
        if len(self.albums) > 0:
            self.albums[0].get_song(0)
        return None

    def find_song(self, title:str, artist:str) -> Song | None:
        """Return a song from any album where the title and artist matches."""
        for a in self.albums:
            return a.find_song(title, artist)
        return None

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

    def ensure_custom_album(self) -> Album:
        """Return the Real & Custom Songs album, merging any legacy custom albums."""
        custom = self.add_album(Album.CustomName)
        for legacy_name in Album.LegacyCustomNames:
            if legacy_name == Album.CustomName:
                continue
            old = self.get_album_by_name(legacy_name)
            if old is None:
                continue
            for song in list(old.songs):
                custom.add_update_song(song)
            self.albums.remove(old)
        return custom

    def add_update_from_midi(
        self, midi_path: Path, track_id: int, album_name: str | None = None
    ) -> Song | None:
        """Load a MIDI file into an album. User MIDI always goes to Real & Custom Songs."""
        midi_path = Path(midi_path)
        if album_name is None or album_name in Album.LegacyCustomNames or album_name == Album.CustomName:
            album = self.ensure_custom_album()
        else:
            album = self.get_album_by_name(album_name)
            if album is None:
                album = self.add_album(album_name)

        if not midi_path.exists():
            return None

        new_song = Song()
        new_song.from_midi_file(str(midi_path), track_id)
        album.add_update_song(new_song)
        return new_song

    def import_user_midi(self, midi_path: Path, track_id: int = 1) -> Song | None:
        """Copy a user MIDI into music/ and add/update it in Real & Custom Songs."""
        midi_path = Path(midi_path)
        if not midi_path.exists() or not midi_path.is_file():
            return None

        suffix = midi_path.suffix.lower()
        if suffix not in (".mid", ".midi"):
            return None

        MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        dest = MUSIC_DIR / midi_path.name
        try:
            if midi_path.resolve() != dest.resolve():
                shutil.copy2(midi_path, dest)
        except OSError as exc:
            print(f"Failed to copy MIDI to {dest}: {exc}")
            return None

        # Prefer a project-relative path for portable songbook pickles
        try:
            store_path = dest.relative_to(Path.cwd())
        except ValueError:
            store_path = dest

        return self.add_update_from_midi(store_path, track_id, Album.CustomName)
