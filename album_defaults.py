from album import Album
from song import Song
from song_book import SongBook

def setup_songbook_albums() -> SongBook:
    # Read the songbook and load the first song
    songbook = SongBook.load()
    if songbook is None:
        # Level 1 starts unlocked
        songbook.add_album("Soundcheck")

        rand_song_c1 = Song()
        rand_song_c1.from_random((32,32), (32,32), 16)
        songbook.add_update_song(rand_song_c1)

        #songbook.add_song_to_album("CMajor")
        #songbook.add_song_to_album("CMinor")
        #songbook.add_song_to_album("BlueNotes") # I IV 5 prog
        #songbook.add_song_to_album("TwoForOne") # II V I prog
        #songbook.add_song_to_album("Wipeout")

        #songbook.add_album("You've Got Rhymthm")
        #songbook.add_song_to_album("Arpegiate") 
        #songbook.add_song_to_album("SpinCycle") # Cycle of 5ths

        #songbook.add_album("Key In Ignition")
        #songbook.add_song_to_album("Roadkill") # Bb scales and arp
        #songbook.add_song_to_album("DeeMinor") # Dm scales and arp

        #songbook.add_album("Standard Practice")
        #songbook.add_song_to_album("4on6") # Wes Montgomery
        #songbook.add_song_to_album("GirlFromIpanema") # 
    songbook.validate()
    songbook.sort()

    return songbook
