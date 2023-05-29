import pygame

# Pygame config constants
PY_RESOLUTION = (640, 360)
PY_SCALE = 2
PY_SCALED_RES = (PY_RESOLUTION[0] * PY_SCALE, PY_RESOLUTION[1] * PY_SCALE)
PY_TARGET_FPS = 75
PY_TITLE = "Isometric world renderer thing"

# Rendering constants
TILE_WIDTH = 8
TILE_HEIGHT = 8
TILE_STAGGER = 4

# Worldgen constants
WORLD_ORIGIN = (int(0), int(0))  # x, z
WORLD_HEIGHT = 50
WORLD_INIT_RADIUS = 2  # Chunk generation radius on world init
WORLD_PRECACHE_CHUNKS = True

# Chunk constants
CHUNK_SIZE = 32
# abhorrent name (it's their "width" when rendering them)
CHUNK_RENDERX = TILE_WIDTH * 2 * CHUNK_SIZE / 2
CHUNK_STAGGER = CHUNK_SIZE * 4

# Sprites
SPRITE_TILE = pygame.image.load("assets/sprites/tile.png")
SPRITE_TILE_X = pygame.image.load("assets/sprites/tile_axis_x.png")
SPRITE_TILE_Z = pygame.image.load("assets/sprites/tile_axis_z.png")

# Debugging stuff
DEBUG_TIMERS = True