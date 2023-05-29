from config import *
from engine.controls import get_control, controls
from engine.camera import Camera
import engine.entities as entities
from engine.world import World
import pygame
import time
from utils import *


class Gamestate:
    def __init__(self):
        pass

    def update(self, dt=0):
        pass

    def draw(self, surf):
        surf.fill("Gray")
