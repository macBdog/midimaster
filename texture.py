import pygame
import os.path

class TextureManager:
    """The textures class handles loading and management of 
        all image resources for the game. The idea is that textures
        are loaded on demand and stay loaded until explicitly unloaded
        or the game is shutdown."""
    def __init__(self, base, subsystems):
        self.cache = {}
        self.base_path = base
        self.sub_paths = []
        self.sub_paths += subsystems

    def Get(self, texture_name):
        if texture_name in self.cache:
            return self.cache[texture_name]

        texture_path = os.path.join(self.base_path, texture_name)
        texture = pygame.image.load(texture_path)
        self.cache[texture_name] = texture
        return texture

    def GetSub(self, sub_name, texture_name):
        if sub_name in self.sub_paths:
            texture_path = os.path.join(sub_name, texture_name)
            return self.Get(texture_path)