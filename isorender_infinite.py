import pygame
import sys
import perlin_noise
from pygame.locals import *
from utils import *

RESOLUTION = (640, 360)
SCALE = 2
SCALED_RESOLUTION = (RESOLUTION[0] * SCALE, RESOLUTION[1] * SCALE)
TARGET_FRAMERATE = 75

MAP_WIDTH_HALF = int(25 / 2)
MAP_ORIGIN_OFFSET = (int(0), int(0))

TILE_WIDTH = 8
TILE_HEIGHT = 8
TILE_STAGGER = 4

SPRITE_TILE = pygame.image.load("tile.png")
SPRITE_TILE_X = pygame.image.load("tile_axis_x.png")
SPRITE_TILE_Z = pygame.image.load("tile_axis_z.png")

# uh not a constant
RENDER_OFFSET = [int(RESOLUTION[0] / 2), int(RESOLUTION[1] / 2)]

# Pygame preconfig
pygame.init()
pygame.display.set_caption("template")
game_window = pygame.display.set_mode(SCALED_RESOLUTION, 0, 32, 0, 1)
game_surface = pygame.Surface(RESOLUTION)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()
frametime = 0


class Tilemap:
    def __init__(self):
        self.map = {}

    def set_tile(self, x=0, y=0, z=0, tile=SPRITE_TILE):
        self.map[f"{x} {y} {z}"] = tile

    def generate_cube(self):
        self.map.clear()

        for z in range(-5, 5):
            for x in range(-5, 5):
                for y in range(-5, 5):
                    self.set_tile(x, y, z)

    def generate_axes(self):
        self.map.clear()

        for x in range(1, 10):
            self.set_tile(x=x, tile=SPRITE_TILE_X)
        for y in range(0, 10):
            self.set_tile(y=y)
        for z in range(1, 10):
            self.set_tile(z=z, tile=SPRITE_TILE_Z)

    def generate(self, noise_octaves=.1, noise_seed=None, noise_multiplier=10):
        self.map.clear()

        noise = perlin_noise.PerlinNoise(
            octaves=noise_octaves, seed=noise_seed)

        for z in range(-MAP_WIDTH_HALF + MAP_ORIGIN_OFFSET[0], MAP_WIDTH_HALF + MAP_ORIGIN_OFFSET[0]):
            for x in range(-MAP_WIDTH_HALF + MAP_ORIGIN_OFFSET[1], MAP_WIDTH_HALF + MAP_ORIGIN_OFFSET[1]):
                y_peak = int(noise([z, x]) * noise_multiplier)

                for actual_y in range(-5, y_peak):
                    actual_x = x - MAP_ORIGIN_OFFSET[1]
                    actual_z = z - MAP_ORIGIN_OFFSET[0]

                    self.set_tile(actual_x, actual_y, actual_z)

                # self.map[f"{x} {y} {z}"] = TILE_SPRITE

        return noise.seed

    def draw(self):
        # tilemap_sorted = sorted(self.map.keys())
        for coords in self.map.keys():
            x, y, z = coords.split(" ")

            # Conversion from strings
            x = int(x)
            y = int(y)
            z = int(z)

            tile_type = self.map[coords]

            tinted = tile_type.copy()

            # TODO moving clouds?????
            # Lower y tiles are shadowed
            shadow_func = 255 + y * 30
            shadow = clamp(shadow_func, 0, 255)

            tinted.fill((shadow, shadow, shadow, 255),
                        special_flags=pygame.BLEND_MULT)

            draw_tile(x, y, z, tinted)


tilemap = Tilemap()


def draw_tile(x, y, z, tile):
    game_surface.blit(tile, (
        RENDER_OFFSET[0] + (x * TILE_WIDTH - z * TILE_WIDTH),
        RENDER_OFFSET[1] + (z * TILE_STAGGER + x *
                            TILE_STAGGER - y * TILE_HEIGHT)
    ))


m_left = False
m_right = False
m_up = False
m_down = False

# just here for show in the debug overlay
n_seed = 0

# Gameloop
while True:
    game_surface.fill((200, 160, 160))
    debug_clear()

    # Event handling
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_a:
                m_left = True
            if event.key == K_d:
                m_right = True
            if event.key == K_w:
                m_up = True
            if event.key == K_s:
                m_down = True
            if event.key == K_F1:
                n_seed = tilemap.generate(
                    noise_octaves=0.1, noise_multiplier=10)
            if event.key == K_F2:
                n_seed = 0
                tilemap.generate_axes()
            if event.key == K_F3:
                n_seed = 0
                tilemap.generate_cube()
        if event.type == KEYUP:
            if event.key == K_a:
                m_left = False
            if event.key == K_d:
                m_right = False
            if event.key == K_w:
                m_up = False
            if event.key == K_s:
                m_down = False

    if m_left:
        RENDER_OFFSET[0] += 5
    if m_right:
        RENDER_OFFSET[0] -= 5
    if m_up:
        RENDER_OFFSET[1] += 5
    if m_down:
        RENDER_OFFSET[1] -= 5

    # Draw to surface
    # draw_tilemap(tilemap)
    tilemap.draw()

    game_window.blit(pygame.transform.scale(
        game_surface, SCALED_RESOLUTION), (0, 0))

    # Debug overlay

    debug_add(f"FPS: {int(clock.get_fps())}")
    debug_add(f"Frametime: {frametime}ms")
    debug_add("")

    debug_add(f"Tiles: {len(tilemap.map)}")
    if n_seed > 0:
        debug_add(f"Map seed: {n_seed}")
        debug_add(f"Map width: {MAP_WIDTH_HALF * 2} tiles")
        debug_add(
            f"Map origin: Z {MAP_ORIGIN_OFFSET[0]}, X {MAP_ORIGIN_OFFSET[1]}")
    debug_add(
        f"Rendering offset: {int(RENDER_OFFSET[0])}, {int(RENDER_OFFSET[1])}")
    debug_add("")

    debug_add("F1: Generate random tilemap")
    debug_add("F2: Generate axes map")
    debug_add("F3: Generate cube map")

    # Draw surface to window
    debug_draw()
    pygame.display.update()
    frametime = clock.tick(TARGET_FRAMERATE)
