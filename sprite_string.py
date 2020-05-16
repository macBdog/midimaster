import pygame
from pygame import Surface
import os.path

class SpriteString(pygame.sprite.DirtySprite):
    def __init__(self, font, text, pos, colour):
        pygame.sprite.DirtySprite.__init__(self)
        self.font = font    
        self.text = text
        self.pos = pos
        self.colour = colour
        self._refresh_text()

    def set_text(self, new_text):
    	self.image.fill((0,0,0))
    	self.text = new_text
    	self._refresh_text()

    def _refresh_text(self):
    	self.image, self.rect = self.font.render(self.text, self.colour)
    	self.rect.x = self.pos[0]
    	self.rect.y = self.pos[1]
    	self.dirty = 0
