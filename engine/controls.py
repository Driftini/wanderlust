import pygame
from pygame.locals import *

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