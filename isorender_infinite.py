import pygame
import sys
import time
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
WORLD_PRECACHE_CHUNKS = True

# Chunk constants
CHUNK_SIZE = 32
# abhorrent name (it's their "width" when rendering them)
CHUNK_RENDERX = TILE_WIDTH * 2 * CHUNK_SIZE / 2
CHUNK_STAGGER = CHUNK_SIZE * 4

# Sprites
SPRITE_TILE = pygame.image.load("tile.png")
SPRITE_TILE_X = pygame.image.load("tile_axis_x.png")
SPRITE_TILE_Z = pygame.image.load("tile_axis_z.png")

# Debugging timers
enable_timers = True  # bad name
debug_timers = {
    "last_worldgen": 0,
    "chunkcache_avg": 0,
    "chunkcache_max": 0,
    "chunkdraw_avg": 0,
    "chunkdraw_max": 0,
}


# Pygame preconfig
pygame.init()  # Pygame is already initialized in utils, this is useless
pygame.display.set_caption(PY_TITLE)
game_window = pygame.display.set_mode(PY_SCALED_RES, vsync=1)
game_surface = pygame.Surface(PY_RESOLUTION)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()
frametime = 0

# Controls stuff (ugly but works)


class Control:
    def __init__(self, key, repeat, description=""):
        self.key = key
        self.repeat = repeat
        self.description = description

        self.state = False
        self.last_state = False


controls = {
    # Dynamic control scheme

    "left": Control(K_a, True),
    "right": Control(K_d, True),
    "up": Control(K_w, True),
    "down": Control(K_s, True),

    "dbg_genworld": Control(K_F1, False, "Generate random world"),
    "dbg_genaxes": Control(K_F2, False, "Generate axes world"),
    "dbg_gencube": Control(K_F3, False, "Generate cube world"),
    "dbg_gengrid": Control(K_F4, False, "Generate grid world"),
    "dbg_toggletimers": Control(K_F12, False, "Toggle debug timers (DISABLED)"),
}


def set_control(action, new_state):
    if controls[action].repeat:
        controls[action].state = new_state
    else:
        if controls[action].last_state:
            controls[action].state = False
        else:
            controls[action].state = new_state

        controls[action].last_state = new_state


def get_control(action):
    return controls[action].state


def update_controls():
    pressed_keys = pygame.key.get_pressed()

    for action in controls:
        # Is the action key being pressed?
        if pressed_keys[controls[action].key]:
            set_control(action, True)
        else:
            set_control(action, False)


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

        # ugh
        self.world = None
        self.camera = None

        # store entities in world or gamestate??

    def update(self, dt=0):
        self.handle_input()

        self.world.update_loaded_chunks()
        self.world.update_loaded_entities()

        self.world.update_entities(dt)

        self.camera.set_target(self.world.entities[0].cube.center)

        self.camera.update()

        self.add_debug_overlay()

    def handle_input(self):
        # if get_control("left"):
        #     self.camera.target_pos[0] -= 5
        # if get_control("right"):
        #     self.camera.target_pos[0] += 5
        # if get_control("up"):
        #     self.camera.target_pos[1] -= 5
        # if get_control("down"):
        #     self.camera.target_pos[1] += 5

        if get_control("dbg_genworld"):
            self.new_world("normal")
        if get_control("dbg_genaxes"):
            self.new_world("axes")
        if get_control("dbg_gencube"):
            self.new_world("cube")
        if get_control("dbg_gengrid"):
            self.new_world("grid")
        # if get_control("dbg_toggletimers"):
        #     enable_timers = not enable_timers

    def draw(self, surf):
        super().draw(surf)

        if self.camera and self.world:
            if enable_timers:
                start_time = time.time()

            self.camera.draw(surf)

            if enable_timers:
                total_time = time.time() - start_time
                debug_timers["chunkdraw_avg"] += total_time
                debug_timers["chunkdraw_avg"] /= 2

                debug_timers["chunkdraw_max"] = max(
                    debug_timers["chunkdraw_max"], total_time
                )

    def new_world(self, gentype="normal", seed=None,
                  y_multiplier=10, noise_octaves=.1):
        if enable_timers:
            start_time = time.time()

        self.world = World(gentype, seed, y_multiplier, noise_octaves)
        self.camera = Camera(PY_RESOLUTION, self.world)

        if enable_timers:
            total_time = time.time() - start_time
            debug_timers["last_worldgen"] = total_time

        self.world.entities.append(
            Mover([0, 1, 0])
        )

    def add_debug_overlay(self):
        debug_add("== World ==")
        # debug_add(f"Tiles count: TODO")
        debug_add(f"Seed: {self.world.seed}")
        debug_add(
            f"Origin: X {WORLD_ORIGIN[0]}, Z {WORLD_ORIGIN[1]}"
        )
        debug_add(f"Initial generation radius: {WORLD_INIT_RADIUS}")
        debug_add(f"Chunk count: {len(self.world.chunks)}")
        debug_add(f"Chunk precaching: {WORLD_PRECACHE_CHUNKS}")

        debug_add("")

        debug_add("== Camera ==")
        debug_add(f"Camera position: {self.camera.get_pos()}")
        debug_add(f"Viewport: {self.camera.get_viewport()}")
        debug_add(
            f"Visible drawables: {len(self.world.get_drawables(self.camera.get_viewport()))}")
        debug_add("")

        debug_add("== Controls ==")
        for action in controls:
            if len(controls[action].description) > 0:
                key = pygame.key.name(controls[action].key)[:2].capitalize()
                debug_add(f"{key}: {controls[action].description}")
        debug_add("")

        if enable_timers:
            self.add_timers_overlay()

    def add_timers_overlay(self):
        debug_add("== Timers ==")
        last_wg = int(debug_timers['last_worldgen'] * 1000)
        debug_add(
            f"Last world generation: {last_wg}ms")

        cc_avg = int(debug_timers["chunkcache_avg"] * 1000)
        cc_max = int(debug_timers["chunkcache_max"] * 1000)
        debug_add(f"Chunk caching: avg {cc_avg}ms, max {cc_max}ms")

        cd_avg = int(debug_timers["chunkdraw_avg"] * 1000)
        cd_max = int(debug_timers["chunkdraw_max"] * 1000)
        debug_add(f"Chunk drawing: avg {cd_avg}ms, max {cd_max}ms")

        debug_add("")


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
        if enable_timers:
            start_time = time.time()

        self.cache.fill((0, 0, 0, 20))

        for coords in self.tiles:
            cx, y, cz = coords.split(" ")
            cx, y, cz = int(cx), int(y), int(cz)

            tile_type = self.tiles[coords]

            tinted = tile_type.copy()

            # Lower y tiles are shadowed
            shadow_func = (y + 5) * 20
            shadow = clamp(shadow_func, 0, 255)

            tinted.fill((shadow, shadow, shadow, 255),
                        special_flags=pygame.BLEND_MULT)

            # cx is altered to center the chunk in the surface,
            # y is altered to make the whole chunk
            # fit vertically in the surface
            draw_tile(self.cache,
                      cx + CHUNK_SIZE - 1, y -
                      WORLD_HEIGHT + (CHUNK_SIZE / 2), cz,
                      tinted)

        if enable_timers:
            total_time = time.time() - start_time
            debug_timers["chunkcache_avg"] += total_time
            debug_timers["chunkcache_avg"] /= 2

            debug_timers["chunkcache_max"] = max(
                debug_timers["chunkcache_max"], total_time
            )

    def get_surf(self):
        # Render the chunk to its cache surface,
        # only when there are changes in its tiles
        if self.tiles != self.tiles_old:
            self.render_cache()
            self.tiles_old = self.tiles

        return self.cache

    def get_surf_size(self):
        return self.cache.get_size()


class World:
    # The world uses world coordinates (x y z),
    # with infinite extension on X and Z axes, WORLD_HEIGHT on Y axis
    def __init__(self, gentype="normal", seed=None,
                 y_multiplier=10, noise_octaves=.1):
        print(f"[WORLD] Initializing new \"{gentype}\" world...")
        self.chunks = {}
        self.noise = None

        self.entities = []
        self.tile_colliders = []  # ?

        self.loaded_chunks = {}
        self.loaded_entities = []
        self.tile_colliders_loaded = []  # ?

        match gentype:
            case "normal":
                self.noise = PerlinNoise(octaves=noise_octaves, seed=seed)
                self.y_multiplier = y_multiplier
                self.seed = self.noise.seed
                print(f"[WORLD] Seed: {self.seed}")

                # Generate chunks within the initial generation radius
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
            case "grid":
                self.seed = "Grid test"

                for x in range(-10, 10):
                    for z in range(-10, 10):
                        if x % 2 != 0:
                            self.set_tile(x=x, z=z, tile=SPRITE_TILE_Z, gen_empty=True)

        if WORLD_PRECACHE_CHUNKS:
            for chunk_coords in self.chunks:
                self.chunks[chunk_coords].get_surf()

        print(f"[WORLD] World init done!")

    # Chunk & tile methods

    def get_chunk_id(self, x, z):
        return f"{math.floor(x / CHUNK_SIZE)} {math.floor(z / CHUNK_SIZE)}"

    def find_chunk(self, x, z):
        # Returns the chunk from X and Z world coordinates (if any)
        chunk_id = self.get_chunk_id(x, z)

        if chunk_id in self.chunks:
            return self.chunks[chunk_id]
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
        if f"{cx} {cz}" not in self.chunks:
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

    def update_loaded_chunks(self):
        # Update the list of loaded chunks
        self.loaded_chunks.clear()

        # temporary
        for chunk in self.chunks:
            # TODO make it based on a radius around player position
            self.loaded_chunks[chunk] = self.chunks[chunk]

    # Entity methods

    def update_loaded_entities(self):
        # Update the list of loaded entities
        self.loaded_entities.clear()

        # temporary
        for entity in self.entities:
            # Check if entity is in a loaded chunk
            if self.get_chunk_id(entity.pos.x, entity.pos.z) in self.loaded_chunks:
                self.loaded_entities.append(entity)

    def update_entities(self, dt=0):
        # Call every loaded entity's update method
        # for entity in self.loaded_entities:
        for entity in self.entities:
            entity.update(dt)

    # Rendering methods

    def get_drawables(self, viewport):
        # Returns all drawables inside of the viewport
        drawables = []  # format: (surf, rect)

        # Get drawable chunks
        for chunk_coords in self.chunks:
            # Get the chunk coords and surface...
            cx, cz = chunk_coords.split(" ")
            cx, cz = int(cx), int(cz)

            c_surf_size = self.chunks[chunk_coords].get_surf_size()

            # Calculate the chunk's draw rect...
            draw_pos = (
                cx * CHUNK_RENDERX - cz * CHUNK_RENDERX,
                cz * CHUNK_STAGGER + cx * CHUNK_STAGGER
            )

            draw_rect = Rect(draw_pos, c_surf_size)

            # And check if the chunk is inside the viewport
            if viewport.colliderect(draw_rect):
                c_surf = self.chunks[chunk_coords].get_surf()
                drawables.append((c_surf, draw_pos))

        # Get drawable entities
        # for entity in self.loaded_entities:
        for entity in self.entities:
            # TODO viewport checks

            # rs = pygame.Surface((20,20))

            # pygame.draw.rect(rs, "Red", Rect(entity.pos.xz, (20,20)))
            # drawables.append((rs, entity.pos.xz))
            drawables.append((entity.sprite, entity.pos.xz))

        return drawables


class Camera:
    def __init__(self, size, world):
        self.size = size
        self.world = world

        self.float_pos = [0.0, 0.0]  # for internal calculations
        self.target_pos = [0.0, 0.0]

    def set_target(self, pos):
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
        # Smooth out movement
        if self.float_pos != self.target_pos:
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


class Cube(pygame.FRect):
    def __init__(self, pos=[0.0, 0.0, 0.0], size=[1, 1, 1]):
        # The FRect properties are used for the X and Z coordinates
        super().__init__(pos[0], pos[2], size[0], size[2])

        self.pos_y = pos[1]
        self.size_y = size[1]

    def collidecube(self, cube):
        if cube.pos_y < self.pos_y < self.size_y:
            super().colliderect(cube)
        else:
            return False


class Entity:
    def __init__(self, pos=[0.0, 0.0, 0.0], size=[1, 1, 1]):
        self.pos = pygame.Vector3(pos)
        self.size = size

        # ONLY for internal usage, don't edit directly
        self.cube = Cube(self.pos.xyz, size)

        self.velocity = pygame.Vector3()
        self.sprite = SPRITE_TILE_X

    def update(self, dt=0):
        # self.pos.x += self.velocity.x
        # self.pos.y += self.velocity.y
        # self.pos.z += self.velocity.z
        self.pos.xyz += self.velocity.xyz

        self.velocity.update()  # clear velocity

        self.cube.topleft = self.pos.xz

class Mover(Entity):
    def __init__(self, pos=[0.0, 0.0, 0.0]):
        super().__init__(pos)

        self.size = [TILE_WIDTH, TILE_HEIGHT, TILE_WIDTH]

    def update(self, dt=0):
        super().update(dt)

        if get_control("left"):
            self.velocity.x -= 1
            self.velocity.z += 1
        if get_control("right"):
            self.velocity.x += 1
            self.velocity.z -= 1
        if get_control("up"):
            self.velocity.z -= 1
            self.velocity.x -= 1
        if get_control("down"):
            self.velocity.z += 1
            self.velocity.x += 1

###


def draw_isometric(surf, x, y, z, sprite):
    surf.blit(sprite, (
        (x - z),
        (z * 1 + x * 1 - y)
    ))


def draw_tile(surf, x, y, z, tile):
    surf.blit(tile, (
        (x * TILE_WIDTH - z * TILE_WIDTH),
        (z * TILE_STAGGER + x * TILE_STAGGER - y * TILE_HEIGHT)
    ))


def draw_world_topdown(surf, world):
    surf_td = pygame.Surface((150, 150))
    surf_td.fill("Black")

    for chunk in world.chunks:
        for tile in world.chunks[chunk].tiles:
            if tile.split(" ")[1] == "0":
                cx, _, cz = tile.split(" ")
                cx, cz = int(cx), int(cz)

                r = pygame.Rect(cx + 75, cz + 75, 1, 1)
                pygame.draw.rect(surf_td, "White", r)

    for entity in world.entities:
        r = pygame.Rect(entity.pos.x + 75, entity.pos.z + 75, 1, 1)
        pygame.draw.rect(surf_td, "Red", r)

    surf_size = surf.get_size()
    surf.blit(surf_td, (surf_size[0] - 150, 0))


gamestates = {
    "play": StatePlay(),
    # "menu": StateMenu()
}

current_gamestate = gamestates["play"]
current_gamestate.new_world()

# should add entity IDs, the list will likely get sorted for rendering
# ent = current_gamestate.world.entities[0]

# Gameloop
while True:
    for event in pygame.event.get():  # this is NOT a control
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    debug_clear()

    debug_add("== General ==")
    debug_add(f"FPS: {int(clock.get_fps())}")
    debug_add(f"Frametime: {frametime}ms")
    debug_add("")

    update_controls()
    current_gamestate.update()
    current_gamestate.draw(game_surface)

    draw_world_topdown(game_surface, current_gamestate.world)

    game_window.blit(pygame.transform.scale(
        game_surface, PY_SCALED_RES), (0, 0)
    )

    debug_draw()

    pygame.display.update()
    frametime = clock.tick(PY_TARGET_FPS)
