from album import Album
from song import Song
from song_book import SongBook

def setup_songbook_albums() -> SongBook:
    # Read the songbook and load the first song
    songbook = SongBook.load()

    if songbook is None:
        # Level 1 starts unlocked
        songbook = SongBook()

        album = songbook.add_album("Soundcheck")
        rand_song_c1 = Song()
        rand_song_c1.from_random((32,32), (32,32), 16)
        album.add_update_song(rand_song_c1)

        #album.add_update_song("CMajor")
        #album.add_update_song("CMinor")
        #album.add_update_song("BlueNotes") # I IV 5 prog
        #album.add_update_song("TwoForOne") # II V I prog
        #album.add_update_song("Wipeout")

        #album = songbook.add_album("You've Got Rhymthm")
        #album.add_update_song("Arpegiate") 
        #album.add_update_song("SpinCycle") # Cycle of 5ths

        #album = songbook.add_album("Key In Ignition")
        #album.add_update_song("Roadkill") # Bb scales and arp
        #album.add_update_song("DeeMinor") # Dm scales and arp

        #album = songbook.add_album("Standard Practice")
        #album.add_update_song("4on6") # Wes Montgomery
        #album.add_update_song("GirlFromIpanema") #
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
