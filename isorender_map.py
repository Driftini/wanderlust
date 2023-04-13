import pygame
import sys
from pygame.locals import *
from utils import *

RESOLUTION = (240, 160)
SCALE = 2
SCALED_RESOLUTION = (RESOLUTION[0] * SCALE, RESOLUTION[1] * SCALE)
TARGET_FRAMERATE = 75
MAP = "map_axes"
TILE_SPRITE = pygame.image.load("tile.png")
TILE_SPRITE_X = pygame.image.load("tile_axis_x.png")
TILE_SPRITE_Z = pygame.image.load("tile_axis_z.png")
TILE_WIDTH = 8
TILE_HEIGHT = 8
TILE_IDK = 4
TILE_OFFSET = (100, 68)

# Pygame preconfig
pygame.init()
pygame.display.set_caption("template")
game_window = pygame.display.set_mode(SCALED_RESOLUTION, 0, 32, 0, 1)
game_surface = pygame.Surface(RESOLUTION)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()
frametime = 0

tilemap = []


def load_tilemap(path):
    mapfile = open(path + ".txt", "r")
    data = mapfile.read()
    mapfile.close()

    data = data.split("\n")

    tmap = []
    for row in data:
        tmap.append(list(row))

    return tmap


def draw_tile(x, y, z, tile):
    game_surface.blit(tile, (
        TILE_OFFSET[0] + x * TILE_WIDTH - z * TILE_WIDTH,
        TILE_OFFSET[1] + z * TILE_IDK + x * TILE_IDK - y * TILE_HEIGHT
    ))
    pass


def draw_tilemap(tmap):
    z = 0
    for row in tmap:
        x = 0
        for col in row:
            tile = ""
            match col:
                case "x":
                    tile = TILE_SPRITE_X
                case "z":
                    tile = TILE_SPRITE_Z
                case _:
                    tile = TILE_SPRITE

            height = 1
            if col.isdigit():
                height = int(col)

            # Y axis
            for y in range(0, max(height, 0)):
                draw_tile(x, y, z, tile)

            x += 1
        z += 1


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
            if event.key == K_SPACE:
                pass
        if event.type == KEYUP:
            if event.key == K_SPACE:
                pass

    # Draw to surface
    tilemap = load_tilemap("map_axes")
    draw_tilemap(tilemap)

    game_window.blit(pygame.transform.scale(
        game_surface, SCALED_RESOLUTION), (0, 0))

    debug_add(f"frametime {frametime}")
    debug_draw()

    # Draw surface to window
    pygame.display.update()
    frametime = clock.tick(TARGET_FRAMERATE)
