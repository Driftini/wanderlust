from config import *
from engine.controls import get_control
import pygame
from utils import *


class Cube(pygame.FRect):
    def __init__(self, pos, size):
        # The FRect properties are used for the X and Z coordinates
        super().__init__(pos[0], pos[2], size[0], size[2])

        self.pos_y = pos[1]
        self.size_y = size[1]

    def collidecube(self, cube):
        # Like Rect.colliderect, but in three dimensions
        if cube.pos_y < self.pos_y < cube.pos_y + cube.size_y:
            # Are both cubes intersecting in the y axis?
            return super().colliderect(cube)
        else:
            return False
    

class Entity:
    def __init__(self, entitylist, pos, size):
        self.entitylist = entitylist
        self.pos = pygame.Vector3(pos)
        self.size = size


        # ONLY for internal usage, don't edit directly
        self.cube = Cube(self.pos.xyz, size)

        self.velocity = pygame.Vector3()
        self.sprite = SPRITE_TILE
        self.visible = True # whether or not the entity gets drawn

    def update(self, dt=0):
        if self.velocity.length() != 0:
            # self.velocity.normalize_ip()

            # self.pos += self.velocity
            self.move()
            self.velocity.update()  # clear velocity

            # this should already happen...?
            # self.cube.topleft = self.pos.xz

    def colliding_entities(self):
        # Get a list of entities colliding with the caller
        collisions = []

        for e in self.entitylist:
            if e is not self:
                if self.cube.collidecube(e.cube):
                    collisions.append(e)

        return collisions

    def move(self):
        # Move cube, while applying compensation for collisions
        contact_sides = {
            "east": False,
            "west": False,
            "north": False,
            "south": False,
            "up": False,
            "down": False
        }

        # Align pos and cube
        self.pos.x = self.cube.x
        self.pos.y = self.cube.pos_y
        self.pos.z = self.cube.y

        # Move along x axis...
        collisions_x = []
        if self.velocity.x != 0:
            self.pos.x += self.velocity.x
            collisions_x = self.colliding_entities()

            for c in collisions_x:
                if self.velocity.x > 0:
                    self.pos.x = c.pos.x - self.size[0]
                    contact_sides["east"] = True
                elif self.velocity.x < 0:
                    self.pos.x = c.pos.x + c.size[0]
                    contact_sides["west"] = True

        # Move along y axis...
        collisions_y = []
        if self.velocity.y != 0:
            self.pos.y += self.velocity.y
            collisions_y = self.colliding_entities()

            for c in collisions_y:
                if self.velocity.y > 0:
                    self.pos.y = c.pos.y - self.size[1]
                    contact_sides["up"] = True
                elif self.velocity.y < 0:
                    self.pos.y = c.pos.y + c.size[1]
                    contact_sides["down"] = True

        # Move along z axis...
        collisions_z = []
        if self.velocity.z != 0:
            self.pos.z += self.velocity.z
            collisions_z = self.colliding_entities()

            for c in collisions_z:
                if self.velocity.z > 0:
                    self.pos.z = c.pos.z - self.size[2]
                    contact_sides["north"] = True
                elif self.velocity.z < 0:
                    self.pos.z = c.pos.z + c.size[2]
                    contact_sides["south"] = True

        # Apply movement
        self.cube.x = self.pos.x
        self.cube.pos_y = self.pos.y
        self.cube.y = self.pos.z

        # Post-move callback
        collisions_all = collisions_x + collisions_y + collisions_z
        self.move_callback(collisions_all, contact_sides)

    def move_callback(self, collisions, contact_sides):
        # Post-move callback
        if contact_sides["east"]:
            self.velocity.x = clamp_max(self.velocity.x, 0)
        if contact_sides["west"]:
            self.velocity.x = clamp_min(self.velocity.x, 0)
        if contact_sides["up"]:
            self.velocity.y = clamp_max(self.velocity.y, 0)
        if contact_sides["down"]:
            self.velocity.y = clamp_min(self.velocity.y, 0)
        if contact_sides["north"]:
            self.velocity.z = clamp_max(self.velocity.y, 0)
        if contact_sides["south"]:
            self.velocity.z = clamp_min(self.velocity.y, 0)
        
        pass

class Collider(Entity):
    def __init__(self, entitylist, pos):
        super().__init__(entitylist, pos, (1,1,1))
        self.visible = False

    def update(self, dt=0):
        # Override Entity.update
        pass