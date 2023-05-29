from engine.entities import Entity
from engine.controls import get_control
import pygame
from utils import *


class Mover(Entity):
    def __init__(self, pos=[0.0, 0.0, 0.0]):
        super().__init__(pos)

        self.size = [TILE_WIDTH, TILE_HEIGHT, TILE_WIDTH]  # tile-sized
        self.speed = .3

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
