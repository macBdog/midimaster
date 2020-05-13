import pygame
from pygame import Surface
from texture import TextureManager
import os.path

class Note:
    """Note is a wrapper around a texture to display it in an animated
    sequence during a game. A note also knows about it's scoring data.
    """

    def __init__(self, texture: Surface, x: int, y: int):
        self.texture = texture
        self.x = x
        self.y = y

    def draw(self, screen: Surface, dt: float, tempo: float):
        screen.blit(self.texture, (self.x, self.y))
        self.x -= dt * tempo

class Notes:
    """Notes manages all the on-screen note representations for a game.
    It is intended to be called by a music manager that creates the notes
    for each piece of music when they should be on-screen.
    """

    def __init__(self, screen: Surface, textures: TextureManager, staff_pos: tuple, tempo: float):
        self.screen = screen
        self.notes = []
        self.textures = textures
        self.pos = staff_pos
        self.origin_note_pitch = 60 # Using middle C4 as the reference note
        self.tempo = tempo
        self.music_font_size = 320
        self.font_music_path = os.path.join("ext", "Musisync.ttf")
        self.font_music = pygame.freetype.Font(self.font_music_path, self.music_font_size)
        self.origin_note_y = self.pos[1] - self.music_font_size * 0.5
        self.pixels_per_pitch = 64
        self.pixels_per_32nd = 24
        self.note_textures = {}
        self.note_textures[32] = self.font_music.render("w")[0]
        self.note_textures[16] = self.font_music.render("h")[0]
        self.note_textures[8] = self.font_music.render("q")[0]
        self.note_textures[4] = self.font_music.render("e")[0]
        self.note_textures[2] = self.font_music.render("s")[0]
        self.note_textures[1] = self.font_music.render("s")[0]

        # Create the barlines and offsets
        self.num_barlines = 3
        self.barlines = []
        self.barline_offsets = []
        for i in range(self.num_barlines):
            self.barlines.append(textures.get("barline.png"))
            self.barline_offsets.append(i * self.pixels_per_32nd * 32)

    def add(self, pitch: int, time: int, length: int):
        if length in self.note_textures:
            pitch_diff = (self.origin_note_pitch - pitch) * self.pixels_per_pitch
            time_diff = time * self.pixels_per_32nd
            newNote = Note(self.note_textures[length], self.pos[0] + time_diff, self.origin_note_y + pitch_diff)
            self.notes.append(newNote)
        else:
            print("Error! Note value of {0} not supported.".format(time))

    def draw(self, dt: float):
        # Draw and update the bar lines
        for i in range(self.num_barlines):
            self.screen.blit(self.barlines[i], (self.barline_offsets[i], self.pos[1] - self.pixels_per_pitch * 3))
            self.barline_offsets[i] -= dt * self.tempo
            if self.barline_offsets[i] < 0:
                self.barline_offsets[i] = self.num_barlines * self.pixels_per_32nd * 32

        # Draw all the current notes
        for note in self.notes:
            note.draw(self.screen, dt, self.tempo)
