import pygame
from pygame import Surface
from texture import TextureManager
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

    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)
        self.dirty = 0
        self.note_id = -1

    def assign(self, note_id: int, texture: Surface, rect, x: int, y: int):
        self.x = x
        self.y = y
        self.image = texture.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.note_id = note_id

    def draw(self, dt: float, tempo: float):
        move_x = -dt * tempo
        self.rect.move_ip(move_x, 0)
        self.x -= move_x
        self.dirty = 1

class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen. There is a pool
    of onscreen notes that recycled when they reach the playhead.
    """

    def __init__(self, devices: MidiDevices, textures: TextureManager, sprites: pygame.sprite.LayeredDirty, staff_pos: tuple, tempo: float):
        self.notes = []
        self.note_pool = []
        self.note_pool_offset = 0
        self.note_pool_size = 32
        self.notes_offset = 0
        self.devices = devices
        self.sprites = sprites
        self.textures = textures
        self.pos = staff_pos
        self.origin_note_pitch = 60 # Using middle C4 as the reference note
        self.tempo = tempo
        self.music_font_size = 220
        self.pixels_per_pitch = 20
        self.pixels_per_32nd = 18
        self.font_music_path = os.path.join("ext", "Musisync.ttf")
        self.font_music = pygame.freetype.Font(self.font_music_path, self.music_font_size)
        self.origin_note_y = self.pos[1] - self.pixels_per_pitch * 2;
        self.origin_note_x = staff_pos[0]
        self.note_textures = {}
        self.note_offsets = {}
        self.add_note_definition(32, "w")
        self.add_note_definition(16, "h")
        self.add_note_definition(8, "q")
        self.add_note_definition(4, "e")
        self.add_note_definition(2, "s")
        self.add_note_definition(1, "s")

        # Create the barlines with 0 being the immovable 0 bar
        self.num_barlines = 4
        self.barlines = []
        for i in range(self.num_barlines):
            barline = textures.get("barline.png")
            barline.rect.x = self.pos[0] + (i * self.pixels_per_32nd * 32)
            barline.rect.y = self.pos[1] - self.pixels_per_pitch * 6
            barline.resize(4, self.pixels_per_pitch * 8)
            self.barlines.append(barline)
            self.sprites.add(barline)

        # Fill the note pool with inactive note sprites to be assigned data when drawn
        for i in range(self.note_pool_size):
            self.note_pool.append(NoteSprite())
            self.sprites.add(self.note_pool[i])

    def add_note_definition(self, num_32nd_notes: int, font_character: str):
        note_texture, rect = self.font_music.render(font_character)
        self.note_textures[num_32nd_notes] = note_texture
        self.note_offsets[num_32nd_notes] = rect

    def add(self, pitch: int, time: int, length: int):
        self.notes.append(Note(pitch, time, length))

        # Automatically assign the first 32 notes that are added from the music
        if self.note_pool_offset < self.note_pool_size:
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
            pitch_diff = (self.origin_note_pitch - note.note) * self.pixels_per_pitch
            time_diff = note.time * self.pixels_per_32nd
            
            note_sprite.assign(self.notes_offset, note_texture, note_offset, self.pos[0] + time_diff, self.origin_note_y + pitch_diff - note_offset.height)
            self.notes_offset += 1
            
    def draw(self, dt: float):
        # Draw and update the bar lines
        for i in range(self.num_barlines):
            if i > 0:
                self.barlines[i].rect.move_ip(-dt * self.tempo, 0)
                if self.barlines[i].rect.x <= self.pos[0]:
                    self.barlines[i].rect.x = self.num_barlines * self.pixels_per_32nd * 32
            self.barlines[i].dirty = 1

        # Draw all the notes in the pool
        for i in range(len(self.note_pool)):
            note_sprite = self.note_pool[i]
            if note_sprite.note_id >= 0:
                note_sprite.draw(dt, self.tempo)

                # Recycle
                if note_sprite.x < self.origin_note_x:
                    note_sprite.note_id = -1
                    note_pool_offset = i
            else:
                self.note_pool_offset = i
