from config import *
from engine.controls import get_control, controls
from engine.camera import Camera
import engine.entities as entities
from engine.world import World
import pygame
import time
from utils import *

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

        # self.camera.set_target(self.world.entities[0].cube.center)
        self.camera.set_target(get_visual_position(
            self.world.entities[0].pos.x,
            self.world.entities[0].pos.y,
            self.world.entities[0].pos.z
        ))

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
            entities.Mover([0, 1, 0])
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