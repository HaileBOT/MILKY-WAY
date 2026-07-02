"""OpenGL drawing helpers for the orbit simulator."""

import math

import pygame
from OpenGL.GL import *

_sphere_cache = {}
_font_cache = {}
_text_texture_cache = {}
pygame.font.init()


def _unit_sphere_rows(stacks, slices):
    rows = []
    for i in range(stacks):
        v0 = i / stacks
        v1 = (i + 1) / stacks
        phi0 = v0 * math.pi - math.pi / 2.0
        phi1 = v1 * math.pi - math.pi / 2.0
        row = []
        for j in range(slices + 1):
            u = j / slices
            theta = u * 2.0 * math.pi
            for phi in (phi0, phi1):
                cx = math.cos(phi) * math.cos(theta)
                cy = math.cos(phi) * math.sin(theta)
                cz = math.sin(phi)
                row.append((cx, cy, cz, cx, cy, cz))
        rows.append(row)
    return rows


def _get_sphere(stacks, slices):
    key = (stacks, slices)
    if key not in _sphere_cache:
        _sphere_cache[key] = _unit_sphere_rows(stacks, slices)
    return _sphere_cache[key]


def draw_sphere(radius, color, stacks=18, slices=24, wireframe=False):
    rows = _get_sphere(stacks, slices)
    glPushMatrix()
    glScalef(radius, radius, radius)
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    for row in rows:
        glBegin(GL_LINE_STRIP if wireframe else GL_TRIANGLE_STRIP)
        for nx, ny, nz, x, y, z in row:
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()
    glPopMatrix()


def draw_banded_sphere(radius, band_colors, stacks=18, slices=24):
    rows = _get_sphere(stacks, slices)
    n = len(band_colors)
    glPushMatrix()
    glScalef(radius, radius, radius)
    for i, row in enumerate(rows):
        glColor3f(*band_colors[int(i / len(rows) * n) % n])
        glBegin(GL_TRIANGLE_STRIP)
        for nx, ny, nz, x, y, z in row:
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()
    glPopMatrix()


def draw_orbit_ring(radius, color, segments=96):
    glBegin(GL_LINE_LOOP)
    glColor3f(*color)
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        glVertex3f(math.cos(t) * radius, 0.0, math.sin(t) * radius)
    glEnd()


def draw_ring_system(inner, outer, color, segments=64, bands=5):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)
    for b in range(bands):
        f0 = b / bands
        f1 = (b + 1) / bands
        r0 = inner + (outer - inner) * f0
        r1 = inner + (outer - inner) * f1
        a = 0.55 - 0.06 * b
        glColor4f(color[0], color[1], color[2], max(a, 0.12))
        glBegin(GL_TRIANGLE_STRIP)
        for i in range(segments + 1):
            t = 2.0 * math.pi * i / segments
            ct, st = math.cos(t), math.sin(t)
            glVertex3f(ct * r0, 0.0, st * r0)
            glVertex3f(ct * r1, 0.0, st * r1)
        glEnd()
    glEnable(GL_LIGHTING)


def draw_glow_shell(radius, color, layers=6):
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    for i in range(layers):
        t = (i + 1) / layers
        draw_sphere(radius * (1.0 + t * 0.5), (color[0], color[1], color[2], (1.0 - t) * 0.15),
                    stacks=10, slices=14)
    glDepthMask(GL_TRUE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING)


def draw_point_cloud(points, color):
    glDisable(GL_LIGHTING)
    glColor3f(*color)
    glBegin(GL_POINTS)
    for x, y, z in points:
        glVertex3f(x, y, z)
    glEnd()
    glEnable(GL_LIGHTING)


def _get_font(size):
    if size not in _font_cache:
        _font_cache[size] = pygame.font.SysFont("consolas,couriernew,monospace", size, bold=True)
    return _font_cache[size]


def make_text_texture(text, size, rgb):
    key = (text, size, rgb)
    if key in _text_texture_cache:
        return _text_texture_cache[key]

    font = _get_font(size)
    color255 = tuple(int(max(0.0, min(1.0, c)) * 255) for c in rgb)
    surf = font.render(text, True, color255).convert_alpha()
    w, h = surf.get_size()
    data = pygame.image.tostring(surf, "RGBA", True)

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    _text_texture_cache[key] = (tex_id, w, h)
    return _text_texture_cache[key]


def draw_hud_text(text, x, y, size=16, rgb=(1.0, 1.0, 1.0), alpha=1.0):
    tex_id, w, h = make_text_texture(text, size, rgb)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glColor4f(1.0, 1.0, 1.0, alpha)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1); glVertex2f(x, y)
    glTexCoord2f(1, 1); glVertex2f(x + w, y)
    glTexCoord2f(1, 0); glVertex2f(x + w, y + h)
    glTexCoord2f(0, 0); glVertex2f(x, y + h)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    return w, h


def draw_flat_bar(x, y, w, h, rgba):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(*rgba)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
