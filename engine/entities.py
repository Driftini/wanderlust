from config import *
from engine.controls import get_control
import pygame
from utils import *


class Cube:
    def __init__(self, pos, size):
        # pos & size are passed as (x, y, z)
        self.pos = pygame.Vector3(pos[0], pos[1], pos[2])
        self.size = pygame.Vector3(size[0], size[1], size[2])

    def check_collision(self, cube):
        # Check if the caller is colliding with a given cube
        # return (
        #     (cube.pos.x <= self.pos.x <= cube.pos.x + cube.size.x)
        #     and (cube.pos.y <= self.pos.y <= cube.pos.y + cube.size.y)
        #     and (cube.pos.z <= self.pos.z <= cube.pos.z + cube.size.z)
        # )

        return (
            min(self.pos.x, self.pos.x + self.size.x) < max(cube.pos.x, cube.pos.x + cube.size.x) and
            min(self.pos.y, self.pos.y + self.size.y) < max(cube.pos.y, cube.pos.y + cube.size.y) and
            min(self.pos.z, self.pos.z + self.size.z) < max(cube.pos.z, cube.pos.z + cube.size.z) and
            max(self.pos.x, self.pos.x + self.size.x) > min(cube.pos.x, cube.pos.x + cube.size.x) and
            max(self.pos.y, self.pos.y + self.size.y) > min(cube.pos.y, cube.pos.y + cube.size.y) and
            max(self.pos.z, self.pos.z + self.size.z) > min(cube.pos.z, cube.pos.z + cube.size.z)
        )


class Entity(Cube):
    def __init__(self, world, pos, size):
        super().__init__(pos, size)
        self.world = world

        self.velocity = pygame.Vector3()
        self.sprite = SPRITE_TILE
        self.visible = True  # whether or not the entity gets drawn

    def update(self, dt=0):
        if self.velocity.length() != 0:
            # self.velocity.normalize_ip()

            self.move()
            self.velocity.update()  # clear velocity

            # this should already happen...?
            # self.cube.topleft = self.pos.xz

    def colliding_tiles(self):
        # Get a list of tiles colliding with the caller
        collisions = []

        # shorter aliases
        p = self.pos
        ps = self.pos + self.size

        for x in range(math.floor(p.x) - PHYS_TILEIMPRECISION, math.floor(ps.x) + PHYS_TILEIMPRECISION):
            for y in range(math.floor(p.y) - PHYS_TILEIMPRECISION, math.floor(ps.y) + PHYS_TILEIMPRECISION):
                for z in range(math.floor(p.z) - PHYS_TILEIMPRECISION, math.floor(ps.z) + PHYS_TILEIMPRECISION):
                    if self.world.get_tile(x, y, z):
                        c = Collider(self.world, (x, y, z))
                        if self.check_collision(c):
                            collisions.append(c)

        debug_add(f"nearby tiles: {len(collisions)}")

        return collisions

    def colliding_entities(self):
        # Get a list of entities colliding with the caller
        collisions = []

        for e in self.world.loaded_entities:
            if e is not self:
                if self.check_collision(e):
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

        # Move along x axis...
        collisions_x = []
        if self.velocity.x != 0:
            self.pos.x += self.velocity.x
            collisions_x = self.colliding_tiles()

            for c in collisions_x:
                if self.velocity.x > 0:
                    self.pos.x = c.pos.x - self.size.x
                    contact_sides["east"] = True
                elif self.velocity.x < 0:
                    self.pos.x = c.pos.x + c.size.x
                    contact_sides["west"] = True

        # Move along y axis...
        collisions_y = []
        if self.velocity.y != 0:
            self.pos.y += self.velocity.y
            collisions_y = self.colliding_tiles()

            for c in collisions_y:
                if self.velocity.y > 0:
                    self.pos.y = c.pos.y - self.size.y
                    contact_sides["up"] = True
                elif self.velocity.y < 0:
                    self.pos.y = c.pos.y + c.size.y
                    contact_sides["down"] = True

        # Move along z axis...
        collisions_z = []
        if self.velocity.z != 0:
            self.pos.z += self.velocity.z
            collisions_z = self.colliding_tiles()

            for c in collisions_z:
                if self.velocity.z > 0:
                    self.pos.z = c.pos.z - self.size.z
                    contact_sides["north"] = True
                elif self.velocity.z < 0:
                    self.pos.z = c.pos.z + c.size.z
                    contact_sides["south"] = True

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


class Collider(Entity):
    def __init__(self, world, pos):
        super().__init__(world, pos, (1, 1, 1))
        self.visible = False

    def update(self, dt=0):
        # Override Entity.update
        pass
