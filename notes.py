import pygame
from pygame import Surface
from texture import TextureManager
from midi_devices import MidiDevices
import os.path
import math

class Note(pygame.sprite.DirtySprite):
    """Note is a wrapper around a texture to display it in an animated
    sequence during a game. A note also knows about it's scoring data.
    """

    def __init__(self, texture: Surface, rect, x: int, y: int):
        pygame.sprite.DirtySprite.__init__(self)
        self.image = texture.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw(self, dt: float, tempo: float):
        self.rect.move_ip(-dt * tempo, 0)
        self.dirty = 1

class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen.
    """

    def __init__(self, devices: MidiDevices, textures: TextureManager, sprites: pygame.sprite.LayeredDirty, staff_pos: tuple, tempo: float):
        self.notes = []
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

    def add_note_definition(self, num_32nd_notes: int, font_character: str):
        note_texture, rect = self.font_music.render(font_character)
        self.note_textures[num_32nd_notes] = note_texture
        self.note_offsets[num_32nd_notes] = rect

    def add(self, pitch: int, time: int, length: int):
        note_texture = self.note_textures.get(length) or self.note_textures[min(self.note_textures.keys(), key=lambda k: abs(k-length))]
        note_offset = self.note_offsets.get(length) or self.note_offsets[min(self.note_offsets.keys(), key=lambda k: abs(k-length))]
        pitch_diff = (self.origin_note_pitch - pitch) * self.pixels_per_pitch
        time_diff = time * self.pixels_per_32nd
        newNote = Note(note_texture, note_offset, self.pos[0] + time_diff, self.origin_note_y + pitch_diff - note_offset.height)
        self.notes.append(newNote)
        self.sprites.add(newNote)

    def draw(self, dt: float):
        # Draw and update the bar lines
        for i in range(self.num_barlines):
            if i > 0:
                self.barlines[i].rect.move_ip(-dt * self.tempo, 0)
                if self.barlines[i].rect.x <= self.pos[0]:
                    self.barlines[i].rect.x = self.num_barlines * self.pixels_per_32nd * 32
            self.barlines[i].dirty = 1

        # Draw all the current notes
        for note in self.notes:
            note.draw(dt, self.tempo)
