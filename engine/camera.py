from config import *
import math
from pygame.locals import *
from utils import *


class Camera:
    def __init__(self, size, world):
        self.size = size
        self.world = world

        self.float_pos = [0.0, 0.0]  # for internal calculations
        self.target_pos = [0.0, 0.0]

        self.followed_entity = None

    def start_following(self, entity):
        self.followed_entity = entity

    def stop_following(self):
        self.followed_entity = None

    def set_target_pos(self, pos):
        # Target position while centering it on screen
        self.target_pos[0] = pos[0] - PY_RESOLUTION[0] / 2
        self.target_pos[1] = pos[1] - PY_RESOLUTION[1] / 2

    def set_pos(self, pos):
        # Instant position change
        self.target_pos = pos
        self.float_pos = self.target_pos

    def get_viewport(self):
        # Returns currently visible area
        return Rect(self.get_pos(), self.size)

    def get_pos(self):
        # Returns rounded position, for use in actual rendering
        return (math.floor(self.float_pos[0]), math.floor(self.float_pos[1]))

    def update(self):
        if self.followed_entity:
            visual_pos = get_visual_position(
                self.followed_entity.pos.x,
                self.followed_entity.pos.y,
                self.followed_entity.pos.z
            )
            self.set_target_pos(visual_pos)

        # Smooth out movement
        if self.float_pos != self.target_pos:
            self.float_pos[0] += (self.target_pos[0] - self.float_pos[0]) / 10
            self.float_pos[1] += (self.target_pos[1] - self.float_pos[1]) / 10

    def draw(self, surf):
        # Draw all currently visible drawables to a given surface
        debug_timers["cameradraw"].start()

        drawables = self.world.get_drawables(self.get_viewport())

        for d in drawables:
            # Apply camera position to the drawables
            actual_pos = (d[1][0] - self.get_pos()[0],
                          d[1][1] - self.get_pos()[1])

            surf.blit(d[0], actual_pos)

        debug_timers["cameradraw"].stop()
