import pygame
from pygame import Surface
from texture import TextureManager

class Note:
    """Note is a wrapper around a texture to display it in an animated
    sequence during a game. A note also knows about it's scoring data.
    """

    def __init__(self, texture: str, x: int, y: int):
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
        self.tempo = tempo
        self.note_textures = []
        self.note_textures.append(textures.get("note_whole.png"))

    def add(self, pitch: int, time: int):
        newNote = Note(self.note_textures[0], self.pos[0] + time, self.pos[1] + pitch)
        self.notes.append(newNote)

    def draw(self, dt: float):
        for note in self.notes:
            note.draw(self.screen, dt, self.tempo)
