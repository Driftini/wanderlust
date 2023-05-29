from config import *
from engine.controls import get_control, controls
from engine.camera import Camera
import game.entities as entities
from engine.gamestates import Gamestate
from engine.world import World
from utils import *


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
        if get_control("dbg_genworld"):
            self.new_world("normal")
        if get_control("dbg_genaxes"):
            self.new_world("axes")
        if get_control("dbg_gencube"):
            self.new_world("cube")
        if get_control("dbg_gengrid"):
            self.new_world("grid")

    def draw(self, surf):
        super().draw(surf)

        if self.camera and self.world:
            self.camera.draw(surf)

    def new_world(self, gentype="normal", seed=None,
                  y_multiplier=10, noise_octaves=.1):
        debug_timers["worldgen"].start()

        self.world = World(gentype, seed, y_multiplier, noise_octaves)
        self.camera = Camera(PY_RESOLUTION, self.world)

        self.world.entities.append(
            entities.Mover([0, 1, 0])
        )

        debug_timers["worldgen"].stop()
        debug_timers["chunkcache"].reset()
        debug_timers["cameradraw"].reset()

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
                key = pygame.key.name(controls[action].key).capitalize()
                debug_add(f"{key}: {controls[action].description}")
        debug_add("")

        if DEBUG_TIMERS:
            self.add_timers_overlay()

    def add_timers_overlay(self):
        debug_add("== Timers ==")
        for timer in debug_timers:
            v_last = debug_timers[timer].get_val()
            v_avg = debug_timers[timer].get_avg()
            v_max = debug_timers[timer].get_max()
            values = f"Max {v_max}ms / Avg {v_avg}ms / Last {v_last}ms"

            if len(debug_timers[timer].label) > 0:
                debug_add(f"{debug_timers[timer].label}: {values}")
            else:
                debug_add(f"{timer}: {values}")

        debug_add("")
