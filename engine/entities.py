from config import *
from engine.controls import get_control
import pygame
from utils import *

class Cube(pygame.FRect):
    def __init__(self, pos=[0.0, 0.0, 0.0], size=[1, 1, 1]):
        # The FRect properties are used for the X and Z coordinates
        super().__init__(pos[0], pos[2], size[0], size[2])

        self.pos_y = pos[1]
        self.size_y = size[1]

    def collidecube(self, cube):
        if cube.pos_y < self.pos_y < self.size_y:
            super().colliderect(cube)
        else:
            return False


class Entity:
    def __init__(self, pos=[0.0, 0.0, 0.0], size=[1, 1, 1]):
        self.pos = pygame.Vector3(pos)
        self.size = size

        # ONLY for internal usage, don't edit directly
        self.cube = Cube(self.pos.xyz, size)

        self.velocity = pygame.Vector3()
        self.sprite = SPRITE_TILE

    def update(self, dt=0):
        if self.velocity.length() != 0:
            # self.velocity.normalize_ip()

            self.pos += self.velocity
            self.velocity.update()  # clear velocity

            self.cube.topleft = self.pos.xz