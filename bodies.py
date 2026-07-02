"""Orbit hierarchy objects for the simulator."""

import math

from OpenGL.GL import *

from geometry import draw_banded_sphere, draw_glow_shell, draw_orbit_ring, draw_ring_system, draw_sphere


class OrbitNode:
    def __init__(self, label, radius, orbit_dist, orbit_speed, color,
                 spin_speed=90.0, axial_tilt=0.0, rings=None, bands=None,
                 emissive=False, parent=None):
        self.label = label
        self.radius = radius
        self.orbit_dist = orbit_dist
        self.orbit_speed = orbit_speed
        self.color = color
        self.spin_speed = spin_speed
        self.axial_tilt = axial_tilt
        self.rings = rings
        self.bands = bands
        self.emissive = emissive
        self.parent = parent
        self.children = []

        self.theta = 0.0
        self.spin = 0.0
        self.path_history = []
        self.max_history = 90

        if parent is not None:
            parent.children.append(self)

    def local_offset(self):
        if self.orbit_dist <= 0.0:
            return (0.0, 0.0, 0.0)
        return (
            math.cos(self.theta) * self.orbit_dist,
            0.0,
            math.sin(self.theta) * self.orbit_dist,
        )

    def world_position(self):
        x, y, z = 0.0, 0.0, 0.0
        node = self
        while node is not None:
            ox, oy, oz = node.local_offset()
            x += ox
            y += oy
            z += oz
            node = node.parent
        return (x, y, z)

    def advance(self, dt, time_scale):
        self.theta = (self.theta + self.orbit_speed * dt * time_scale) % (2.0 * math.pi)
        self.spin = (self.spin + self.spin_speed * dt * time_scale) % 360.0

        if self.orbit_dist > 0.0:
            self.path_history.append(self.world_position())
            if len(self.path_history) > self.max_history:
                self.path_history.pop(0)

        for child in self.children:
            child.advance(dt, time_scale)

    def render(self, size_scale, star_glow_color=None, pulse=0.0):
        glPushMatrix()
        ox, oy, oz = self.local_offset()
        glTranslatef(ox, oy, oz)

        visible_radius = self.radius * size_scale

        if self.emissive:
            glDisable(GL_LIGHTING)
            draw_sphere(visible_radius * (1.0 + 0.03 * pulse), self.color, stacks=22, slices=28)
            draw_glow_shell(visible_radius, star_glow_color or self.color)
            glEnable(GL_LIGHTING)
        else:
            glPushMatrix()
            glRotatef(self.axial_tilt, 0.0, 0.0, 1.0)
            glRotatef(self.spin, 0.0, 1.0, 0.0)
            if self.bands:
                draw_banded_sphere(visible_radius, self.bands, stacks=20, slices=26)
            else:
                draw_sphere(visible_radius, self.color, stacks=16, slices=20)
            if self.rings:
                inner_mult, outer_mult, ring_color = self.rings
                draw_ring_system(visible_radius * inner_mult, visible_radius * outer_mult, ring_color)
            glPopMatrix()

        for child in self.children:
            child.render(size_scale, star_glow_color, pulse)

        glPopMatrix()

    def render_orbit_guides(self, base_color):
        glPushMatrix()
        if self.orbit_dist > 0.0:
            draw_orbit_ring(self.orbit_dist, base_color)
            ox, oy, oz = self.local_offset()
            glTranslatef(ox, oy, oz)
        for child in self.children:
            child.render_orbit_guides(base_color)
        glPopMatrix()

    def render_trail(self, alpha_max=0.5):
        if len(self.path_history) >= 2:
            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBegin(GL_LINE_STRIP)
            n = len(self.path_history)
            for i, (x, y, z) in enumerate(self.path_history):
                a = (i / n) * alpha_max
                glColor4f(self.color[0], self.color[1], self.color[2], a)
                glVertex3f(x, y, z)
            glEnd()
            glEnable(GL_LIGHTING)
        for child in self.children:
            child.render_trail(alpha_max)

    def flatten(self):
        out = [self]
        for child in self.children:
            out.extend(child.flatten())
        return out


def build_system():
    star = OrbitNode("Aster", 1.35, 0.0, 0.0, (1.0, 0.82, 0.25), emissive=True)

    mercury = OrbitNode("Ferrum", 0.10, 2.3, 1.05, (0.60, 0.58, 0.55), spin_speed=8, parent=star)
    venus = OrbitNode("Bruma", 0.19, 3.4, 0.62, (0.85, 0.68, 0.40), spin_speed=-4, axial_tilt=177, parent=star)

    terra = OrbitNode("Terra", 0.21, 4.8, 0.40, (0.20, 0.50, 0.90), spin_speed=140, axial_tilt=23, parent=star)
    OrbitNode("Luna", 0.05, 0.42, 2.4, (0.72, 0.72, 0.70), spin_speed=40, parent=terra)

    ares = OrbitNode("Ares", 0.15, 6.4, 0.27, (0.80, 0.34, 0.20), spin_speed=130, axial_tilt=25, parent=star)
    OrbitNode("Phobia", 0.03, 0.30, 3.8, (0.55, 0.48, 0.44), spin_speed=60, parent=ares)
    OrbitNode("Nyx", 0.025, 0.46, 2.7, (0.50, 0.46, 0.42), spin_speed=55, parent=ares)

    jove_bands = [(0.78, 0.63, 0.45), (0.85, 0.70, 0.52), (0.70, 0.53, 0.37), (0.88, 0.75, 0.58)]
    jove = OrbitNode("Jove", 0.52, 9.0, 0.14, (0.78, 0.63, 0.45), spin_speed=210, axial_tilt=3,
                      bands=jove_bands, parent=star)
    OrbitNode("Kallis", 0.045, 0.75, 3.0, (0.90, 0.86, 0.30), spin_speed=90, parent=jove)
    OrbitNode("Vesper", 0.038, 0.98, 2.2, (0.80, 0.78, 0.90), spin_speed=80, parent=jove)

    ring_bands = [(0.83, 0.75, 0.55), (0.90, 0.83, 0.62), (0.76, 0.65, 0.45)]
    saturnian = OrbitNode("Cronis", 0.44, 11.8, 0.095, (0.83, 0.75, 0.55), spin_speed=190, axial_tilt=27,
                           bands=ring_bands, rings=(1.4, 2.4, (0.80, 0.70, 0.52, 0.55)), parent=star)
    OrbitNode("Tethyon", 0.06, 0.85, 1.9, (0.87, 0.79, 0.40), spin_speed=45, parent=saturnian)

    OrbitNode("Ourania", 0.31, 14.5, 0.045, (0.55, 0.83, 0.90), spin_speed=170, axial_tilt=98,
              rings=(1.5, 2.0, (0.55, 0.78, 0.85, 0.35)), parent=star)
    OrbitNode("Neridus", 0.29, 17.5, 0.022, (0.24, 0.40, 0.88), spin_speed=165, axial_tilt=28, parent=star)

    return star
