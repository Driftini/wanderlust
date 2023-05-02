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


class Gamestate:
    def __init__(self):
        pass

    def update(self, dt=0):
        pass

    def draw(self, surf):
        surf.fill("Gray")


class StatePlay(Gamestate):
    def __init__(self):
        super().__init__()

        # self.surf = pygame.Surface(PY_RESOLUTION)
        self.world = None
        self.camera = None

    def update(self, dt=0):
        # handle input
        pass

    def draw(self, surf):
        super().draw(surf)

        if camera and world:
            self.camera.draw(surf)

    def new_world(self, gentype="normal", seed=None,
                  y_multiplier=10, noise_octaves=.1):
        self.world = World(gentype, seed, y_multiplier, noise_octaves)
        self.camera = Camera(self.world)

    def handle_inputs(self):
        m_left = False
        m_right = False
        m_up = False
        m_down = False

        # left off here


class Chunk:
    # Chunks use chunk coordinates (cx cz),
    # spanning from 0 to CHUNK_SIZE on the X and Z axes
    def __init__(self):
        self.tiles = {}

        # it has to be different from self.tiles,
        # else it never renders to cache
        self.tiles_old = None

        self.cache = pygame.Surface(
            (
                TILE_WIDTH * 2 * CHUNK_SIZE,
                (CHUNK_SIZE * TILE_STAGGER) * 2 +
                WORLD_HEIGHT * TILE_HEIGHT + 4
                # this is an actual mess (+4 is a bandaid fix for
                # an unwanted vertical offset in tile drawing)
            ), flags=SRCALPHA
        )

    def convert_coords(self, x, z):
        # Convert world coords to chunk coords
        chunk_x = x % CHUNK_SIZE
        chunk_z = z % CHUNK_SIZE

        return chunk_x, chunk_z

    def get_tile(self, x, y, z):
        cx, cz = self.convert_coords(x, z)

        return self.tiles[f"{cx} {y} {cz}"]

    def set_tile(self, x, y, z, tile=SPRITE_TILE):
        if (0 <= x <= CHUNK_SIZE) and (0 <= y <= WORLD_HEIGHT) and (0 <= z <= CHUNK_SIZE):
            cx, cz = self.convert_coords(x, z)

            self.tiles[f"{cx} {y} {cz}"] = tile

    def render_cache(self):
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
            draw_tile(self.cache,
                      cx + CHUNK_SIZE - 1, y -
                      WORLD_HEIGHT + (CHUNK_SIZE / 2), cz,
                      tinted)

    def get_surf(self):
        # Render the chunk to its cache surface,
        # only when there are changes in its tiles
        if self.tiles != self.tiles_old:
            self.render_cache()
            self.tiles_old = self.tiles

        return self.cache


class World:
    # The world uses world coordinates (x y z),
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

                for x in range(0, 10):
                    self.set_tile(x=x, tile=SPRITE_TILE_X, gen_empty=True)
                for y in range(0, 10):
                    self.set_tile(y=y, gen_empty=True)
                for z in range(0, 10):
                    self.set_tile(z=z, tile=SPRITE_TILE_Z, gen_empty=True)
            case "cube":
                self.seed = "Cube Test"

                for z in range(-5, 5):
                    for x in range(-5, 5):
                        for y in range(-5, 5):
                            self.set_tile(x, y, z, gen_empty=True)

        print(f"[WORLD] World init done!")

    def find_chunk(self, x, z):
        # Returns the chunk from X and Z world coordinates (if any)
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
        # Places a tile at the given coordinates,
        # optionally generating the rest of the chunk as well
        chunk = self.find_chunk(x, z)

        if chunk:
            chunk.set_tile(x, y, z, tile)
        elif gen_empty:
            # If the chunk doesn't exist and gen_empty is set,
            # generate it and retry
            cx, cz = Chunk.convert_coords(Chunk, x, z)
            self.generate_chunk(cx, cz)

            self.set_tile(x, y, z, tile)  # retry placing the tile

    def generate_chunk(self, cx, cz):
        # Generate a new chunk at CX, CZ
        if f"{cx} {cz}" not in self.chunks.keys():
            # Only continue if the chunk doesn't already exist
            chunk = self.chunks[f"{cx} {cz}"] = Chunk()

            if self.noise:
                print(f"[WORLDGEN] Generating chunk: CX {cx},\tCZ {cz}...")

                for z in range(0, CHUNK_SIZE):
                    # Calc corresponding world Z
                    wz = WORLD_ORIGIN[1] + z + cz * CHUNK_SIZE

                    for x in range(0, CHUNK_SIZE):
                        # Calc corresponding world X
                        wx = WORLD_ORIGIN[0] + x + cx * CHUNK_SIZE

                        # Peak height for this coordinate
                        y_peak = int(self.noise([wz, wx]) * self.y_multiplier)

                        # Clamp minimum height to avoid holes in the world
                        y_peak = clamp_min(y_peak + 5, 1)

                        for actual_y in range(0, y_peak):
                            chunk.set_tile(x, actual_y, z)

    def get_drawables(self, viewport):
        # Returns all drawables inside of the viewport
        drawables = []  # format: (surf, rect)

        # Get drawable chunks
        for chunk_coords in self.chunks.keys():
            # Get the chunk coords and surface...
            cx, cz = chunk_coords.split(" ")
            cx, cz = int(cx), int(cz)

            c_surf = self.chunks[chunk_coords].get_surf()

            # Get the chunk's draw rect...
            draw_pos = (
                cx * CHUNK_RENDERX - cz * CHUNK_RENDERX,
                cz * CHUNK_STAGGER + cx * CHUNK_STAGGER
            )

            draw_rect = Rect(draw_pos, c_surf.get_size())

            # And check if the chunk is inside the viewport
            if viewport.colliderect(draw_rect):
                drawables.append((c_surf, draw_pos))

        return drawables


class Camera:
    def __init__(self, size, world):
        self.size = size
        self.world = world

        self.float_pos = [0.0, 0.0]  # for internal calculations
        self.target_pos = [0.0, 0.0]

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
        # Smooth out movement
        self.float_pos[0] += (self.target_pos[0] - self.float_pos[0]) / 10
        self.float_pos[1] += (self.target_pos[1] - self.float_pos[1]) / 10

    def draw(self, surf):
        # Draw all currently visible drawables to a given surface
        drawables = self.world.get_drawables(self.get_viewport())

        for d in drawables:
            # Apply camera postion to the drawables' rects
            actual_pos = (d[1][0] - self.get_pos()[0],
                          d[1][1] - self.get_pos()[1])

            surf.blit(d[0], actual_pos)

###


world = World()
cam = Camera(PY_RESOLUTION, world)


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
                cam.world = world  # actually sucks
            if event.key == K_F2:
                world = World("axes")
                cam.world = world
            if event.key == K_F3:
                world = World("cube")
                cam.world = world
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
        cam.target_pos[0] -= 5
    if m_right:
        cam.target_pos[0] += 5
    if m_up:
        cam.target_pos[1] -= 5
    if m_down:
        cam.target_pos[1] += 5

    # Draw to screen

    cam.update()
    cam.draw(game_surface)

    game_window.blit(pygame.transform.scale(
        game_surface, PY_SCALED_RES), (0, 0)
    )

    # Debug overlay

    debug_add("== General ==")
    debug_add(f"FPS: {int(clock.get_fps())}")
    debug_add(f"Frametime: {frametime}ms")
    debug_add("")

    debug_add("== World ==")
    # debug_add(f"Tiles count: TODO")
    debug_add(f"World seed: {world.seed}")
    debug_add(f"Chunk count: {len(world.chunks)}")
    debug_add(
        f"World origin: X {WORLD_ORIGIN[0]}, Z {WORLD_ORIGIN[1]}")
    debug_add("")

    debug_add("== Camera ==")
    debug_add(f"Camera position: {cam.get_pos()}")
    debug_add(f"Viewport: {cam.get_viewport()}")
    debug_add(
        f"Visible drawables: {len(world.get_drawables(cam.get_viewport()))}")
    debug_add("")

    debug_add("== Controls ==")
    debug_add("F1: Generate random world")
    debug_add("F2: Generate axes world")
    debug_add("F3: Generate cube world")

    # Draw surface to window
    debug_draw()
    pygame.display.update()
    frametime = clock.tick(PY_TARGET_FPS)
