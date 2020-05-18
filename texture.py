import pygame
from pygame import Surface
import os.path

class SpriteShape(pygame.sprite.DirtySprite):
    def __init__(self, size: tuple, colour: tuple):
        pygame.sprite.DirtySprite.__init__(self)
        self.image = pygame.Surface(size)
        self.image.fill(colour)
        self.rect = self.image.get_rect()
        self.dirty = 1

    def set_alpha(self, alpha: int):
        self.image.set_alpha(alpha)
        self.dirty = 1

class SpriteTexture(pygame.sprite.DirtySprite):
    def __init__(self, texture_path: str):
        pygame.sprite.DirtySprite.__init__(self)
        self.image = pygame.image.load(texture_path)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.dirty = 1

    def tint(self, colour: tuple): 
        """ Modifies the supplied texture by adding colour onto surface.
        :param surface: The surface to be modified
        :param colour: The RGB colour value to be added
		""" 
        self.image.fill((255, 255, 255, 255), None, pygame.BLEND_RGBA_MULT)
        self.image.fill(colour[0:3] + (0,), None, pygame.BLEND_RGBA_ADD)
        self.dirty = 1

    def resize(self, width: int, height: int):
        x_cache = self.rect.x
        y_cache = self.rect.y
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x_cache
        self.rect.y = y_cache
        self.rect.width = width
        self.rect.height = height
        self.dirty = 1

    def set_alpha(self, alpha: int):
        self.image.set_alpha(alpha)
        self.dirty = 1

class TextureManager:
    """The textures class handles loading and management of 
        all image resources for the game. The idea is that textures
        are loaded on demand and stay loaded until explicitly unloaded
        or the game is shutdown."""
    def __init__(self, base, subsystems):
        self.base_path = base
        self.sub_paths = []
        self.sub_paths += subsystems

    def get(self, texture_name: str) -> SpriteTexture:
        texture_path = os.path.join(self.base_path, texture_name)
        return SpriteTexture(texture_path)

    def get_sub(self, sub_name: str, texture_name:str) -> SpriteTexture:
        if sub_name in self.sub_paths:
            texture_path = os.path.join(sub_name, texture_name)
            return self.get(texture_path)
