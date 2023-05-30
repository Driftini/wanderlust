from config import *
from engine.entities import Collider
from perlin_noise import PerlinNoise
import pygame
from pygame.locals import *
from utils import *

class Chunk:
    # Tiles inside chunks use chunk coordinates (cx, cz),
    # spanning from 0 to CHUNK_SIZE on the X and Z axes
    # Chunks themselves have chunk IDs (ALSO cx cz)
    def __init__(self):
        self.tiles = {}

        # it has to be different from self.tiles,
        # else it never renders to cache
        self.tiles_old = None

        self.cache = pygame.Surface(
            (
                TILE_WIDTH * 2 * CHUNK_SIZE,
                (CHUNK_SIZE * TILE_STAGGER) * 2 + WORLD_HEIGHT * TILE_HEIGHT + 4
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
        if (0 <= y <= WORLD_HEIGHT):
            cx, cz = self.convert_coords(x, z)

            self.tiles[f"{cx} {y} {cz}"] = tile

    def render_cache(self):
        debug_timers["chunkcache"].start()

        # self.cache.fill((0, 0, 0, 20))

        for coords in self.tiles:
            cx, y, cz = coords.split(" ")
            cx, y, cz = int(cx), int(y), int(cz)

            tile_type = self.tiles[coords]

            sprite = tile_type.copy()

            # Lower y tiles are shadowed
            shadow_func = (y + 5) * 20
            shadow = clamp(shadow_func, 0, 255)

            sprite.fill((shadow, shadow, shadow, 255),
                        special_flags=pygame.BLEND_MULT)

            # cx is altered to center the chunk in the surface,
            # y is altered to make the whole chunk
            # fit vertically in the surface
            visual_pos = get_visual_position(
                cx + CHUNK_SIZE - 1,
                y - WORLD_HEIGHT + (CHUNK_SIZE / 2),
                cz
            )

            self.cache.blit(sprite, visual_pos)

        debug_timers["chunkcache"].stop()

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
        self.noise = None
        self.chunks = {}
        self.entities = []
        self.tile_colliders = [] # stored separately from entities to speed up updates

        self.loaded_chunks = {}
        self.loaded_entities = []
        self.loaded_tile_colliders = []

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
                        for y in range(0, 10):
                            self.set_tile(x, y, z, gen_empty=True)
            case "grid":
                self.seed = "Grid test"

                for x in range(-50, 50):
                    for z in range(-50, 50):
                        if (x + z) % 2 != 0:
                            self.set_tile(x=x, z=z, tile=SPRITE_TILE_X, gen_empty=True)
                        else:
                            self.set_tile(x=x, z=z, tile=SPRITE_TILE_Z, gen_empty=True)

        if WORLD_PRECACHE_CHUNKS:
            for chunk_id in self.chunks:
                self.chunks[chunk_id].get_surf()

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
            self.spawn_entity(Collider, [x, y, z])
            chunk.set_tile(x, y, z, tile)
        elif gen_empty:
            # If the chunk doesn't exist and gen_empty is set,
            # generate it and retry
            chunk_id = self.get_chunk_id(x, z)
            cx, cz = chunk_id.split(" ")
            self.generate_chunk(cx, cz)

            self.set_tile(x, y, z, tile)  # retry placing the tile


    def generate_chunk(self, cx, cz):
        # Generate a new chunk at CX, CZ
        if f"{cx} {cz}" not in self.chunks:
            # Only continue if the chunk doesn't already exist
            print(f"[WORLDGEN] Creating chunk: CX {cx},\tCZ {cz}...")

            chunk = self.chunks[f"{cx} {cz}"] = Chunk()
            
            if self.noise:
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

                        for y in range(0, y_peak):
                            self.set_tile(wx, y, wz)

    def update_loaded_chunks(self):
        # Update the list of loaded chunks
        self.loaded_chunks.clear()

        # temporary
        for chunk in self.chunks:
            # TODO make it based on a radius around player position
            self.loaded_chunks[chunk] = self.chunks[chunk]

    # Entity methods

    def spawn_entity(self, entityclass, pos=[0,0,0]):
        if entityclass is Collider:
            collider = entityclass([], pos)
            self.tile_colliders.append(collider)

            return collider
        else:
            entity = entityclass(self.entities + self.tile_colliders, pos)
            self.entities.append(entity)

            return entity

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
        for chunk_id in self.chunks:
            # Get the chunk ID and surface...
            cx, cz = chunk_id.split(" ")
            cx, cz = int(cx), int(cz)

            c_surf_size = self.chunks[chunk_id].get_surf_size()

            # Calculate the chunk's draw rect...

            # The magic numbers that are subtracted fix the massive offset
            # that is normally there
            draw_pos = (
                cx * CHUNK_RENDERX - cz * CHUNK_RENDERX - 248,
                cz * CHUNK_STAGGER + cx * CHUNK_STAGGER - 396
            )

            draw_rect = Rect(draw_pos, c_surf_size)

            # And check if the chunk is inside the viewport
            if viewport.colliderect(draw_rect):
                c_surf = self.chunks[chunk_id].get_surf()
                drawables.append((c_surf, draw_pos))

        # Get drawable entities
        # for entity in self.loaded_entities:
        for entity in self.entities:
            if entity.visible:
                draw_pos = get_visual_position(
                    entity.pos.x,
                    entity.pos.y,
                    entity.pos.z
                )

                entity_surf_size = entity.sprite.get_size()

                draw_rect = Rect(draw_pos, entity_surf_size)

                if viewport.colliderect(draw_rect):
                    drawables.append((entity.sprite, draw_pos))

        return drawables