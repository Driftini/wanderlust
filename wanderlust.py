from config import *
from engine.controls import update_controls
from game.gamestates import StatePlay
import pygame
from pygame.locals import *
import sys
from utils import *

# Pygame preconfig
pygame.init()  # Pygame is already initialized in utils, this is useless
pygame.display.set_caption(PY_TITLE)
game_window = pygame.display.set_mode(PY_SCALED_RES, vsync=1)
game_surface = pygame.Surface(PY_RESOLUTION)
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()
frametime = 0

gamestates = {
    "play": StatePlay()
}

current_gamestate = gamestates["play"]
current_gamestate.new_world()

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

    game_window.blit(pygame.transform.scale(
        game_surface, PY_SCALED_RES), (0, 0)
    )

    debug_draw()

    pygame.display.update()
    frametime = clock.tick(PY_TARGET_FPS)
