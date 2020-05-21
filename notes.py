import pygame
from pygame import Surface
from texture import TextureManager
from texture import SpriteShape
from midi_devices import MidiDevices
import os.path
import math

class Note():
    """Note is a POD style container for a note in a piece of music with representation."""

    def __init__(self, note: int, time: int, length: int):
        self.note = note
        self.time = time
        self.length = length

class NoteSprite(pygame.sprite.DirtySprite):
    """NoteSprite ais the visual representation of a note using the DirtySprite parent class. 
        It owns an index into the Notes class note array of  note data for scoring and timing.
    """

    def __init__(self, default_texture: Surface):
        pygame.sprite.DirtySprite.__init__(self)
        self.dirty = 0
        self.note_id = -1
        self.image = default_texture
        self.rect = self.image.get_rect()

    def assign(self, note_id: int, texture: Surface, note: int, time: int, length: int, pitch_pos: int):
        self.note = note
        self.time = time
        self.length = length
        self.pitch_pos = pitch_pos
        self.image = texture.copy()
        self.rect = self.image.get_rect()
        self.note_id = note_id

    def recycle(self):
        self.rect.x = 9999
        self.rect.y = 9999
        self.note_id = -1
        self.dirty = 1

    def draw(self, music_time: float, origin_note_x: int, notes_on: dict):
        if self.note_id >= 0:
            self.rect.x = origin_note_x + self.time - music_time
            self.rect.y = self.pitch_pos
            self.dirty = 1

            if self.time < music_time:
                notes_on[self.note] = self.time + self.length
                self.recycle()

class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen. There is a pool
    of onscreen notes that recycled when they reach the playhead.
    """

    def __init__(self, devices: MidiDevices, textures: TextureManager, sprites: pygame.sprite.LayeredDirty, staff_pos: tuple, note_positions: list, incidentals: dict):
        self.notes = []
        self.note_pool = []
        self.note_pool_offset = 0
        self.note_pool_size = 32
        self.notes_offset = 0
        self.devices = devices
        self.sprites = sprites
        self.textures = textures
        self.incidentals = incidentals
        self.note_positions = note_positions
        self.pos = staff_pos
        self.origin_note_pitch = 60 # Using middle C4 as the reference note
        self.music_font_size = 190
        self.pixels_per_pitch = 10
        self.pixels_per_32nd = 12
        self.font_music_path = os.path.join("ext", "Musisync.ttf")
        self.font_music = pygame.freetype.Font(self.font_music_path, self.music_font_size)
        self.origin_note_y = self.pos[1] + self.pixels_per_pitch * 10;
        self.origin_note_x = staff_pos[0]
        self.note_textures = {}
        self.note_offsets = {}
        self.notes_on = {}
        self.add_note_definition(32, "w")
        self.add_note_definition(16, "h")
        self.add_note_definition(8, "q")
        self.add_note_definition(4, "e")
        self.add_note_definition(2, "s")
        self.add_note_definition(1, "s")

        # Create the barlines with 0 being the immovable 0 bar
        self.num_barlines = 8
        self.barlines = []
        self.bartimes = []
        for i in range(self.num_barlines):
            barline = SpriteShape((4, self.pixels_per_pitch * 16), (0, 0, 0))
            self.barlines.append(barline)
            self.sprites.add(barline)
            self.bartimes.append(i * self.pixels_per_32nd * 32);
            
        # Fill the note pool with inactive note sprites to be assigned data when drawn
        for i in range(self.note_pool_size):
            self.note_pool.append(NoteSprite(self.note_textures[32]))
            self.sprites.add(self.note_pool[i])

    def add_note_definition(self, num_32nd_notes: int, font_character: str):
        note_texture, rect = self.font_music.render(font_character)
        self.note_textures[num_32nd_notes] = note_texture
        self.note_offsets[num_32nd_notes] = rect

    def add(self, pitch: int, time: int, length: int):
        self.notes.append(Note(pitch, time, length))

        # Automatically assign the first 32 notes that are added from the music
        if self.note_pool_offset < self.note_pool_size - 1:
            self.assign_note()

    def assign_note(self):
        # Search for an inactive note in the pool to assign to
        if self.note_pool[self.note_pool_offset].note_id >= 0:
            for i in range(len(self.note_pool)):
                if self.note_pool[i].note_id < 0:
                    self.note_pool_offset = i
                    break

        # This will evaluate true when there is a piece of music with 32 notes in 2 bars
        if self.note_pool[self.note_pool_offset].note_id >= 0:
            print("Failed to find an inactive note sprite in the pool!")

        if self.notes_offset < len(self.notes):
            note_sprite = self.note_pool[self.note_pool_offset]
            note = self.notes[self.notes_offset]

            note_texture = self.note_textures.get(note.length) or self.note_textures[min(self.note_textures.keys(), key=lambda k: abs(k-note.length))]
            note_offset = self.note_offsets.get(note.length) or self.note_offsets[min(self.note_offsets.keys(), key=lambda k: abs(k-note.length))]
            note_diff = self.note_positions[note.note % 12]
            num_octaves = (note.note - 60) // 12
            per_octave = self.note_positions[12]
            pitch_diff = -note_diff - (num_octaves * per_octave)
            note_time = note.time * self.pixels_per_32nd
            
            note_sprite.assign(self.notes_offset, note_texture, note.note, note_time, note.length, self.origin_note_y + pitch_diff - note_offset.height)
            self.notes_offset += 1
            
    def draw(self, music_time) -> dict:
        """ Draw and update the bar lines and all notes in the pool.
        Return a dictionary keyed on note numbers with value of the end music time note length
        """
        for i in range(self.num_barlines):
            self.barlines[i].rect.x = self.origin_note_x + self.bartimes[i] - music_time
            self.barlines[i].rect.y = self.pos[1] - self.pixels_per_pitch * 12
            self.barlines[i].dirty = 1
            if self.bartimes[i] < music_time:
                self.bartimes[i] += self.pixels_per_32nd * 32
                              
        # Draw all the notes in the pool
        for i in range(len(self.note_pool)):
            self.note_pool[i].draw(music_time, self.origin_note_x, self.notes_on)

        return self.notes_on
