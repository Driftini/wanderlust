import pygame
import sys
from perlin_noise import PerlinNoise
from pygame.locals import *
from utils import *

# Pygame config constants
PY_RESOLUTION = (640, 360)
PY_SCALE = 2
PY_SCALED_RES = (PY_RESOLUTION[0] * PY_SCALE, PY_RESOLUTION[1] * PY_SCALE)
PY_TARGET_FPS = 75
PY_TITLE = "Isometric world renderer thing"

# Tile rendering constants
TILE_WIDTH = 8
TILE_HEIGHT = 8
TILE_STAGGER = 4

# Worldgen constants
WORLD_ORIGIN = (int(0), int(0))  # x, z
WORLD_HEIGHT = 50
WORLD_INIT_RADIUS = 2  # Chunk generation radius on world init

# Chunk constants
CHUNK_SIZE = 32
# abhorrent name (it's their "width" when rendering them)
CHUNK_RENDERX = TILE_WIDTH * 2 * CHUNK_SIZE / 2
CHUNK_STAGGER = CHUNK_SIZE * 4

# uh not a constant
RENDER_OFFSET = [int(PY_RESOLUTION[0] / 2), int(PY_RESOLUTION[1] / 2)]

# Sprites
SPRITE_TILE = pygame.image.load("tile.png")
SPRITE_TILE_X = pygame.image.load("tile_axis_x.png")
SPRITE_TILE_Z = pygame.image.load("tile_axis_z.png")

# Pygame preconfig
pygame.init()
pygame.display.set_caption(PY_TITLE)
game_window = pygame.display.set_mode(PY_SCALED_RES, 0, 32, 0, 1)
game_surface = pygame.Surface(PY_RESOLUTION)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()
frametime = 0

ALREADY_GEN = set()


class Chunk:
    # Chunks use chunk coordinates,
    # spanning from 0 to CHUNK_SIZE on the X and Z axes
    def __init__(self):
        self.tiles = {}

        # it has to be different from self.tiles, else it never renders to cache
        self.tiles_old = None

        self.cache = pygame.Surface(
            (
                TILE_WIDTH * 2 * CHUNK_SIZE,
                (CHUNK_SIZE * TILE_STAGGER) * 2 +
                WORLD_HEIGHT * TILE_HEIGHT + 4
                # this is an actual mess (+4 is a bandaid fix for an unwanted vertical offset in tile drawing)
            ), flags=SRCALPHA
            # (1000, 1000), flags=SRCALPHA
        )

    # Convert world coords to chunk coords
    def convert_coords(self, x, z):
        chunk_x = x % CHUNK_SIZE
        chunk_z = z % CHUNK_SIZE

        return chunk_x, chunk_z

    def get_tile(self, x, y, z):
        cx, cz = self.convert_coords(x, z)

        return self.tiles[f"{cx} y {cz}"]

    def set_tile(self, x, y, z, tile=SPRITE_TILE):
        if (0 <= x <= CHUNK_SIZE) and (0 <= y <= WORLD_HEIGHT) and (0 <= z <= CHUNK_SIZE):
            cx, cz = self.convert_coords(x, z)

            self.tiles[f"{cx} {y} {cz}"] = tile

    def render_cache(self):
        # self.cache.fill((0, 0, 0, 10))
        self.cache.fill((0, 0, 0, 0))

        for coords in self.tiles.keys():
            cx, y, cz = coords.split(" ")
            cx, y, cz = int(cx), int(y), int(cz)

            tile_type = self.tiles[coords]

            tinted = tile_type.copy()

            # Lower y tiles are shadowed
            shadow_func = (y + 5) * 20
            shadow = clamp(shadow_func, 0, 255)

            tinted.fill((shadow, shadow, shadow, 255),
                        special_flags=pygame.BLEND_MULT)

            # cx is altered to center the chunk in the surface
            # y is altered to make the whole chunk fit vertically in the surface
            draw_tile(self.cache, cx + CHUNK_SIZE - 1, y -
                      WORLD_HEIGHT + (CHUNK_SIZE / 2), cz, tinted)

    def get_surf(self):
        if self.tiles != self.tiles_old:
            self.render_cache()
            self.tiles_old = self.tiles

        return self.cache


class World:
    # The world uses world coordinates,
    # with infinite extension on X and Z axes, WORLD_HEIGHT on Y axis
    def __init__(self, gentype="normal", seed=None,
                 y_multiplier=10, noise_octaves=.1):
        print(f"[WORLD] Initializing new \"{gentype}\" world...")
        self.chunks = {}
        self.noise = None

        match gentype:
            case "normal":
                self.noise = PerlinNoise(octaves=noise_octaves, seed=seed)
                self.y_multiplier = y_multiplier
                self.seed = self.noise.seed
                print(f"[WORLD] Seed: {self.seed}")

                for cz in range(-WORLD_INIT_RADIUS, WORLD_INIT_RADIUS):
                    for cx in range(-WORLD_INIT_RADIUS, WORLD_INIT_RADIUS):
                        self.generate_chunk(cx, cz)
            case "axes":
                self.seed = "Axes Test"

                for x in range(1, 10):
                    self.set_tile(x=x, tile=SPRITE_TILE_X, gen_empty=True)
                for y in range(0, 10):
                    self.set_tile(y=y, gen_empty=True)
                for z in range(1, 10):
                    self.set_tile(z=z, tile=SPRITE_TILE_Z, gen_empty=True)
            case "cube":
                self.seed = "Cube Test"

                for z in range(-5, 5):
                    for x in range(-5, 5):
                        for y in range(-5, 5):
                            self.set_tile(x, y, z, gen_empty=True)

        print(f"[WORLD] World init done!")

    # Get chunk from X and Z world coordinates
    def find_chunk(self, x, z):
        chunk_coords = (math.floor(x / CHUNK_SIZE), math.floor(z / CHUNK_SIZE))
        chunk_key = f"{chunk_coords[0]} {chunk_coords[1]}"

        if chunk_key in self.chunks.keys():
            return self.chunks[chunk_key]
        else:
            return False  # maybe unnecessary

    def get_tile(self, x, y, z):
        chunk = self.find_chunk(x, z)

        return chunk.get_tile(x, y, z)

    def set_tile(self, x=0, y=0, z=0, tile=SPRITE_TILE, gen_empty=False):
        chunk = self.find_chunk(x, z)

        if chunk:
            chunk.set_tile(x, y, z, tile)
        # TODO gen chunk if needed
        elif gen_empty:
            cx, cz = Chunk.convert_coords(Chunk, x, z)
            self.generate_chunk(cx, cz)

            self.set_tile(x, y, z, tile)  # retry placing the tile

    def generate_chunk(self, cx, cz):
        if not f"{cx} {cz}" in self.chunks.keys():  # if chunk doesn't already exist
            chunk = self.chunks[f"{cx} {cz}"] = Chunk()
            
            if self.noise:
                print(f"[WORLDGEN] Generating chunk: CX {cx}\tCZ {cz}...")

                for z in range(0, CHUNK_SIZE):
                    # Corresponding world Z
                    wz = WORLD_ORIGIN[1] + z + cz * CHUNK_SIZE

                    for x in range(0, CHUNK_SIZE):
                        wx = WORLD_ORIGIN[0] + x + cx * CHUNK_SIZE

                        y_peak = int(self.noise([wz, wx]) * self.y_multiplier)

                        for actual_y in range(0, clamp_min(y_peak + 5, 1)):
                            # for actual_y in range(0, WORLD_HEIGHT):
                            chunk.set_tile(x, actual_y, z)

    def draw(self, surf):
        for chunk_coords in self.chunks.keys():
            cx, cz = chunk_coords.split(" ")
            cx, cz = int(cx), int(cz)

            c_surf = self.chunks[chunk_coords].get_surf()
            c_srect = c_surf.get_rect()

            draw_pos = (
                (RENDER_OFFSET[0] + cx * CHUNK_RENDERX - cz * CHUNK_RENDERX),
                (RENDER_OFFSET[1] + cz * CHUNK_STAGGER + cx * CHUNK_STAGGER)
            )

            surf.blit(c_surf, draw_pos)


world = World()


def draw_tile(surf, x, y, z, tile):
    surf.blit(tile, (
        (x * TILE_WIDTH - z * TILE_WIDTH),
        (z * TILE_STAGGER + x * TILE_STAGGER - y * TILE_HEIGHT)
    ))


m_left = False
m_right = False
m_up = False
m_down = False

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
                world = World("normal")
            if event.key == K_F2:
                world = World("axes")
            if event.key == K_F3:
                world = World("cube")
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
    world.draw(game_surface)

    game_window.blit(pygame.transform.scale(
        game_surface, PY_SCALED_RES), (0, 0)
    )

    # Debug overlay

    debug_add(f"FPS: {int(clock.get_fps())}")
    debug_add(f"Frametime: {frametime}ms")
    debug_add("")

    debug_add(f"Tiles count: TODO")
    if world.seed:
        debug_add(f"World seed: {world.seed}")
        debug_add(f"Chunk count: {len(world.chunks)}")
        debug_add(
            f"World origin: Z {WORLD_ORIGIN[0]}, X {WORLD_ORIGIN[1]}")
    debug_add(
        f"Rendering offset: {int(RENDER_OFFSET[0])}, {int(RENDER_OFFSET[1])}")
    debug_add("")

    debug_add("F1: Generate random world")
    debug_add("F2: Generate axes world")
    debug_add("F3: Generate cube world")

    # Draw surface to window
    debug_draw()
    pygame.display.update()
    frametime = clock.tick(PY_TARGET_FPS)
