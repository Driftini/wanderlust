from engine.entities import Entity
from engine.controls import get_control
import pygame
from utils import *


class Mover(Entity):
    def __init__(self, pos):
        super().__init__(pos, [1, 1, 1])

        self.size = [TILE_WIDTH, TILE_HEIGHT, TILE_WIDTH]  # tile-sized
        self.speed = .3
        self.sprite = SPRITE_TILE_Z

    def update(self, dt=0):
        super().update(dt)

        if get_control("left"):
            self.velocity.x -= self.speed
            self.velocity.z += self.speed
        if get_control("right"):
            self.velocity.x += self.speed
            self.velocity.z -= self.speed
        if get_control("up"):
            self.velocity.z -= self.speed
            self.velocity.x -= self.speed
        if get_control("down"):
            self.velocity.z += self.speed
            self.velocity.x += self.speed
