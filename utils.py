import pygame
import math

pygame.init()


def f_pass():
    pass


def interpolate_avg(old, new, speed):
    return old + (new - old) * speed


def clamp(val, min, max):
    if val < min:
        return min
    elif val > max:
        return max
    else:
        return val


def clamp_min(val, min):
    if val < min:
        return min
    else:
        return val


def clamp_max(val, max):
    if val > max:
        return max
    else:
        return val


def rel_bool(val):  # shit name (relative bool??????)
    if val:
        return 1
    else:
        return -1


def get_scaled_mousepos(scale):
    mpos = pygame.mouse.get_pos()

    return (mpos[0] / scale, mpos[1] / scale)


def get_distance(pos1, pos2):
    distX = pos2[0] - pos1[0]
    distY = pos2[1] - pos1[1]

    return math.sqrt((distX ** 2) + (distY ** 2))


def get_angle(pos1, pos2):
    diffX = pos2[0] - pos1[0]
    diffY = pos2[1] - pos1[1]

    if diffX == 0:  # TODO might be able to remove this
        diffX += 1

    angle = math.atan(diffY / diffX)

    if pos2[0] < pos1[0]:
        angle += math.pi

    return angle


# Dynamic debug print
debug_font = pygame.font.Font(None, 24)
debug_lines = []


def debug_clear():
    debug_lines.clear()


def debug_add(val):
    debug_lines.append(val)


def debug_draw(x=8, y=8):
    line_height = 16
    line_counter = 0
    surf_render = pygame.display.get_surface()  # final surface to render to

    for l in debug_lines:
        # temporary surface for text alone
        surf_text = debug_font.render(str(l), True, "White")
        rect_text = surf_text.get_rect(
            topleft=(x, y + line_counter * line_height))  # text position

        pygame.draw.rect(surf_render, "Black", rect_text)
        surf_render.blit(surf_text, rect_text)

        line_counter += 1
