"""Orbit Hierarchy Simulator
==========================
A pseudo-3D simulation of a star system that demonstrates hierarchical
transformations with the OpenGL matrix stack: every satellite's on-screen
position is computed relative to its parent, whose position is in turn
relative to *its* parent, all the way up to the star at the root.

Controls
    SPACE        pause / resume the simulation clock
    R            reverse the direction of time
    UP / DOWN    speed up / slow down time
    = / -        scale every planet up / down
    LEFT DRAG    orbit the camera
    WHEEL        zoom
    ESC          quit
"""

import math
import random
import sys

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
from pygame.locals import DOUBLEBUF, OPENGL

from bodies import build_system
from config import (
    STARFIELD_COUNT,
    STARFIELD_MAX_RADIUS,
    STARFIELD_MIN_RADIUS,
    THEME,
    WINDOW_H,
    WINDOW_W,
)
from controls import AppState, handle_event
from geometry import draw_flat_bar, draw_hud_text, draw_point_cloud


def make_starfield(count, min_r, max_r):
    pts = []
    for _ in range(count):
        theta = random.uniform(0, 2 * math.pi)
        phi = math.acos(random.uniform(-1, 1))
        r = random.uniform(min_r, max_r)
        pts.append((
            r * math.sin(phi) * math.cos(theta),
            r * math.sin(phi) * math.sin(theta),
            r * math.cos(phi),
        ))
    return pts


def configure_opengl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glClearColor(*THEME["background"])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 0.96, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.05, 0.05, 0.07, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])


def set_camera(distance, pitch_deg, yaw_deg):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, distance)
    glRotatef(pitch_deg, 1.0, 0.0, 0.0)
    glRotatef(yaw_deg, 0.0, 1.0, 0.0)


def draw_hud(width, height, time_scale, paused, size_scale):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    draw_hud_text("ORBIT HIERARCHY SIMULATOR", 20, height - 34, size=20, rgb=THEME["hud_main"])

    status = f"TIME x{time_scale:+.2f}" + ("  [PAUSED]" if paused else "")
    draw_hud_text(status, 20, height - 60, size=14, rgb=THEME["hud_dim"])
    draw_hud_text(f"PLANET SCALE x{size_scale:.2f}", 20, height - 80, size=14, rgb=THEME["hud_dim"])

    bar_x, bar_y, bar_w, bar_h = 300, height - 58, 200, 12
    draw_flat_bar(bar_x, bar_y, bar_w, bar_h, THEME["bar_back"])
    fill_ratio = min(abs(time_scale) / 10.0, 1.0)
    fill_color = THEME["bar_fill"] if time_scale >= 0 else (0.85, 0.4, 0.35)
    draw_flat_bar(bar_x, bar_y, bar_w * fill_ratio, bar_h, (*fill_color, 0.9))

    help_lines = [
        "[SPACE] pause   [R] reverse   [UP/DOWN] speed",
        "[=/-] scale planets   [drag] rotate   [wheel] zoom",
    ]
    for i, line in enumerate(help_lines):
        draw_hud_text(line, 20, 40 - i * 20, size=12, rgb=THEME["hud_dim"], alpha=0.85)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_W, WINDOW_H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Orbit Hierarchy Simulator")
    configure_opengl()

    star_root = build_system()
    backdrop = make_starfield(STARFIELD_COUNT, STARFIELD_MIN_RADIUS, STARFIELD_MAX_RADIUS)

    state = AppState()
    clock = pygame.time.Clock()

    while state.running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            handle_event(event, state)

        if not state.paused:
            star_root.advance(dt, state.time_scale)
            state.elapsed += dt * state.time_scale

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, WINDOW_W / float(WINDOW_H), 0.1, 130.0)

        set_camera(state.cam_distance, state.cam_pitch, state.cam_yaw)

        glDepthMask(GL_FALSE)
        glDisable(GL_LIGHTING)
        draw_point_cloud(backdrop, THEME["stars"])
        glEnable(GL_LIGHTING)
        glDepthMask(GL_TRUE)

        glDisable(GL_LIGHTING)
        star_root.render_orbit_guides(THEME["orbit_line"])
        star_root.render_trail(alpha_max=0.4)
        glEnable(GL_LIGHTING)

        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
        pulse = math.sin(state.elapsed * 2.2)
        star_root.render(state.size_scale, star_glow_color=star_root.color, pulse=pulse)

        draw_hud(WINDOW_W, WINDOW_H, state.time_scale, state.paused, state.size_scale)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
