"""Keyboard and mouse handling for the orbit simulator."""

from dataclasses import dataclass

from pygame.locals import (
    KEYDOWN,
    K_DOWN,
    K_EQUALS,
    K_ESCAPE,
    K_MINUS,
    K_r,
    K_SPACE,
    K_UP,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
    MOUSEMOTION,
    QUIT,
)


@dataclass
class AppState:
    time_scale: float = 1.0
    size_scale: float = 1.0
    paused: bool = False
    cam_distance: float = -24.0
    cam_pitch: float = 42.0
    cam_yaw: float = 0.0
    dragging: bool = False
    last_mouse: tuple[int, int] = (0, 0)
    elapsed: float = 0.0
    running: bool = True


def handle_event(event, state: AppState):
    if event.type == QUIT:
        state.running = False
    elif event.type == KEYDOWN:
        if event.key == K_ESCAPE:
            state.running = False
        elif event.key == K_SPACE:
            state.paused = not state.paused
        elif event.key == K_r:
            state.time_scale *= -1.0
        elif event.key == K_UP:
            state.time_scale *= 1.4
        elif event.key == K_DOWN:
            state.time_scale /= 1.4
        elif event.key == K_EQUALS:
            state.size_scale = min(state.size_scale * 1.15, 4.0)
        elif event.key == K_MINUS:
            state.size_scale = max(state.size_scale / 1.15, 0.25)
    elif event.type == MOUSEBUTTONDOWN:
        if event.button == 1:
            state.dragging = True
            state.last_mouse = event.pos
        elif event.button == 4:
            state.cam_distance = min(state.cam_distance + 1.2, -6.0)
        elif event.button == 5:
            state.cam_distance = max(state.cam_distance - 1.2, -65.0)
    elif event.type == MOUSEBUTTONUP:
        if event.button == 1:
            state.dragging = False
    elif event.type == MOUSEMOTION and state.dragging:
        dx = event.pos[0] - state.last_mouse[0]
        dy = event.pos[1] - state.last_mouse[1]
        state.cam_yaw += dx * 0.35
        state.cam_pitch += dy * 0.35
        state.last_mouse = event.pos
