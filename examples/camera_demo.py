#!/usr/bin/env python3
"""
Demo of the camera system with parallax scrolling.

Arrow keys to move camera, P to toggle perspective/orthographic mode.
Shows multiple windows at different depths creating a parallax effect.
"""

import pygame
import pyunicodegame


def main():
    root = pyunicodegame.init("Camera Demo", width=80, height=25, bg=(10, 10, 30, 255))

    # Scene is 3x wider than viewport for scrolling
    scene_width = 240

    # Create layers at different depths
    # Background - far away, moves slowest
    bg = pyunicodegame.create_window("bg", 0, 0, scene_width, 25, z_index=0, bg=(5, 5, 20, 255))
    bg.depth = 2.0

    # Midground - moderate depth
    mid = pyunicodegame.create_window("mid", 0, 0, scene_width, 25, z_index=5, bg=(0, 0, 0, 0))
    mid.depth = 1.0

    # Foreground - at camera plane, moves 1:1
    fg = pyunicodegame.create_window("fg", 0, 0, scene_width, 25, z_index=10, bg=(0, 0, 0, 0))
    fg.depth = 0.0

    # UI - fixed, doesn't move with camera (same size as viewport)
    ui = pyunicodegame.create_window("ui", 0, 0, 80, 25, z_index=100, bg=(0, 0, 0, 0))
    ui.fixed = True

    # Enable perspective mode and start camera in the middle of the scene
    # Scene is 240 cells, viewport is 80, so center camera at (240-80)/2 = 80 cells
    # At 10 pixels per cell, that's 800 pixels
    start_x = (scene_width - 80) // 2 * 10
    pyunicodegame.set_camera(x=start_x, y=0, mode="perspective", depth_scale=0.1)

    # Camera movement speed (pixels per second)
    camera_speed = 150

    def update(dt):
        # Smooth camera movement with held keys
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx -= camera_speed * dt
        if keys[pygame.K_RIGHT]:
            dx += camera_speed * dt
        if keys[pygame.K_UP]:
            dy -= camera_speed * dt
        if keys[pygame.K_DOWN]:
            dy += camera_speed * dt
        if dx or dy:
            pyunicodegame.move_camera(dx, dy)

    def on_key(key):
        if key == pygame.K_p:
            # Toggle perspective/orthographic
            x, y, mode, depth_scale = pyunicodegame.get_camera()
            new_mode = "orthographic" if mode == "perspective" else "perspective"
            pyunicodegame.set_camera(mode=new_mode)
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Get camera state for display
        cx, cy, mode, depth_scale = pyunicodegame.get_camera()

        # Background layer - distant stars (move slowest)
        bg.surface.fill(bg._bg)
        # Stars scattered across the wide scene
        stars = [
            # Original area
            (10, 5), (25, 8), (40, 3), (55, 10), (70, 6),
            (15, 15), (35, 18), (50, 14), (65, 20), (78, 12),
            (5, 22), (30, 20), (45, 22), (60, 19), (75, 23),
            # Middle section
            (95, 5), (110, 8), (125, 4), (140, 11), (155, 7),
            (100, 16), (118, 19), (135, 13), (150, 21), (165, 14),
            (90, 23), (108, 18), (130, 22), (148, 17), (162, 20),
            # Right section
            (180, 6), (195, 9), (210, 3), (225, 12), (235, 8),
            (185, 17), (200, 14), (215, 20), (228, 15), (238, 22),
            (175, 21), (192, 23), (208, 18), (222, 24), (232, 19),
        ]
        for sx, sy in stars:
            bg.put(sx, sy, "*", (100, 100, 150))

        # Midground - mountains/hills (moderate parallax)
        mid.surface.fill(mid._bg)
        # Draw mountain ranges across the scene
        def draw_mountain(base_x, peak_y, width):
            for i in range(width):
                offset = abs(i - width // 2)
                y = peak_y + offset
                mid.put(base_x + i, y, "^", (60, 80, 60))

        # Mountains spread across scene
        draw_mountain(5, 16, 5)
        draw_mountain(20, 14, 7)
        draw_mountain(40, 16, 5)
        draw_mountain(55, 13, 9)
        draw_mountain(75, 15, 5)
        draw_mountain(95, 14, 7)
        draw_mountain(115, 16, 5)
        draw_mountain(135, 12, 9)
        draw_mountain(160, 15, 5)
        draw_mountain(180, 14, 7)
        draw_mountain(200, 16, 5)
        draw_mountain(220, 13, 7)

        # Trees in midground
        trees = [
            (12, 19), (18, 20), (32, 19), (38, 20), (48, 19),
            (52, 20), (68, 19), (72, 20), (88, 19), (102, 20),
            (112, 19), (128, 20), (145, 19), (158, 20), (172, 19),
            (188, 20), (205, 19), (218, 20), (232, 19),
        ]
        for tx, ty in trees:
            mid.put(tx, ty - 1, "^", (40, 100, 40))
            mid.put(tx, ty, "|", (80, 60, 40))

        # Foreground - ground level (moves 1:1 with camera)
        fg.surface.fill(fg._bg)
        # Draw ground across entire scene
        for x in range(scene_width):
            fg.put(x, 22, "_", (80, 80, 60))
            fg.put(x, 23, ".", (60, 60, 40))
            fg.put(x, 24, ".", (50, 50, 30))

        # Objects spread across the foreground
        # Houses
        for hx in [20, 80, 150, 210]:
            fg.put(hx, 21, "#", (150, 100, 50))
            fg.put(hx + 1, 21, "#", (150, 100, 50))

        # Campfires
        for cfx in [40, 120, 180]:
            fg.put(cfx, 21, "*", (255, 200, 100))

        # Signs/markers
        for sx in [60, 100, 140, 200]:
            fg.put(sx, 21, "|", (120, 80, 40))
            fg.put(sx, 20, "-", (100, 70, 35))

        # Player marker (center of scene)
        fg.put(120, 21, "@", (255, 255, 100))

        # UI layer - fixed, shows controls and status (all at top)
        ui.surface.fill(ui._bg)
        ui.put_string(2, 0, "CAMERA DEMO - Parallax Scrolling", (200, 200, 255))
        ui.put_string(2, 1, "Arrow keys: Move   P: Toggle mode   Q: Quit", (150, 150, 150))

        # Status and layer info on same line
        mode_str = mode.upper()
        status = f"Cam: ({cx:.0f},{cy:.0f}) {mode_str}"
        ui.put_string(2, 2, status, (100, 100, 100))
        ui.put_string(35, 2, "BG:2.0", (80, 80, 100))
        ui.put_string(45, 2, "MID:1.0", (60, 80, 60))
        ui.put_string(56, 2, "FG:0.0", (100, 100, 60))

    pyunicodegame.run(update=update, render=render, on_key=on_key)


if __name__ == "__main__":
    main()
