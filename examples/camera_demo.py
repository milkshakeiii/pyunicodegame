#!/usr/bin/env python3
"""
Demo of the camera system with parallax scrolling.

Arrow keys to move camera, P to toggle perspective/orthographic mode.
Shows multiple windows at different depths creating a parallax effect.
"""

import random
import pygame
import pyunicodegame


def main():
    root = pyunicodegame.init("Camera Demo", width=80, height=25, bg=(10, 10, 30, 255))

    scene_width = 240
    ground_y = 22

    # --- Create layers ---

    # Stars (fixed, doesn't scroll)
    stars_layer = pyunicodegame.create_window(
        "stars", 0, 0, scene_width, 50, z_index=0,
        bg=(5, 5, 20, 255), scale=0.6, fixed=True
    )

    # Mountains (far background, slow parallax)
    mountains_layer = pyunicodegame.create_window(
        "mountains", 0, 0, scene_width, 25, z_index=1, bg=(0, 0, 0, 0), depth=4.0
    )

    # Trees (midground, moderate parallax)
    trees_layer = pyunicodegame.create_window(
        "trees", 0, 0, scene_width, 25, z_index=5, bg=(0, 0, 0, 0), depth=1.0
    )

    # Foreground (moves 1:1 with camera)
    fg = pyunicodegame.create_window(
        "fg", 0, 0, scene_width, 25, z_index=10, bg=(0, 0, 0, 0), depth=0.0
    )

    # UI (fixed overlay)
    ui = pyunicodegame.create_window(
        "ui", 0, 0, 80, 25, z_index=100, bg=(0, 0, 0, 0), fixed=True
    )

    # --- Stars (twinkling animation) ---

    for _ in range(150):
        sx = random.randint(0, scene_width - 1)
        sy = random.randint(0, 49)
        b = 120 + random.randint(0, 60)  # base brightness

        star = pyunicodegame.create_sprite("✦", x=sx, y=sy, fg=(b, b, b + 40))
        star.add_frame("✧", fg=(b - 30, b - 30, b + 20))
        star.add_frame("·", fg=(b - 60, b - 60, b))
        star.add_frame("✧", fg=(b - 30, b - 30, b + 20))

        speed = 0.3 + random.random() * 0.5
        twinkle = pyunicodegame.create_animation(
            "twinkle", frame_indices=[0, 1, 2, 1, 0, 0, 0], frame_duration=speed
        )
        star.add_animation(twinkle)
        star.play_animation("twinkle")
        stars_layer.add_sprite(star)

    # --- Mountains ---

    def create_mountain(window, center_x, peak_y, color):
        """Create a mountain as a single multi-line sprite using ◢◣█ characters."""
        height = ground_y - peak_y
        max_width = 2 + (height - 1) * 2

        rows = []
        for i in range(height):
            width = 2 + i * 2
            padding = (max_width - width) // 2
            if width == 2:
                line = " " * padding + "◢◣" + " " * padding
            else:
                line = " " * padding + "◢" + "█" * (width - 2) + "◣" + " " * padding
            rows.append(line)

        mountain = pyunicodegame.create_sprite(
            "\n".join(rows), x=center_x - (max_width // 2 - 1), y=peak_y, fg=color
        )
        window.add_sprite(mountain)

    for cx, py, color in [
        (15, 14, (45, 60, 50)), (45, 12, (38, 52, 42)), (80, 15, (42, 58, 48)),
        (110, 11, (35, 48, 38)), (140, 13, (40, 55, 45)), (175, 12, (38, 52, 42)),
        (210, 14, (45, 60, 50)), (235, 13, (35, 50, 40)),
    ]:
        create_mountain(mountains_layer, cx, py, color)

    # --- Trees ---

    round_tree = """
 ███
█████
 ███
  █"""

    pine_tree = """
  ◢◣
 ◢██◣
◢████◣
  ██"""

    tree_positions = [15, 35, 55, 75, 95, 115, 135, 155, 175, 195, 215, 235]
    for i, tx in enumerate(tree_positions):
        if i % 2 == 0:
            tree = pyunicodegame.create_sprite(
                round_tree, x=tx - 2, y=ground_y - 4, fg=(35, 90, 35),
                char_colors={"█": (30, 85, 30)}
            )
        else:
            tree = pyunicodegame.create_sprite(
                pine_tree, x=tx - 3, y=ground_y - 4, fg=(25, 75, 30),
                char_colors={"◢": (25, 75, 30), "◣": (25, 75, 30), "█": (30, 80, 35)}
            )
        trees_layer.add_sprite(tree)

    # --- Ground ---

    for y, color in [(ground_y, (45, 70, 35)), (ground_y + 1, (70, 50, 30)), (ground_y + 2, (55, 40, 25))]:
        ground = pyunicodegame.create_sprite("█" * scene_width, x=0, y=y, fg=color)
        fg.add_sprite(ground)

    # --- Houses ---

    house_pattern = """
◢█◣
█░█"""

    for hx in [25, 85, 145, 205]:
        house = pyunicodegame.create_sprite(
            house_pattern, x=hx - 1, y=ground_y - 2, fg=(160, 110, 60),
            char_colors={"◢": (140, 80, 40), "◣": (140, 80, 40), "█": (160, 110, 60)}
        )
        fg.add_sprite(house)

    # --- Campfires ---

    for cfx in [50, 120, 180]:
        fire = pyunicodegame.create_sprite("✱", x=cfx, y=ground_y - 1, fg=(255, 180, 50), emissive=True)
        fg.add_sprite(fire)

    # --- Signs ---

    sign_pattern = """
▬▬▬
 │"""

    for sx in [70, 160, 220]:
        sign = pyunicodegame.create_sprite(
            sign_pattern, x=sx - 1, y=ground_y - 2, fg=(100, 75, 40),
            char_colors={"▬": (120, 90, 50), "│": (100, 75, 40)}
        )
        fg.add_sprite(sign)

    # --- Player ---

    player = pyunicodegame.create_sprite("@", x=100, y=ground_y - 1, fg=(255, 255, 100))
    fg.add_sprite(player)

    # --- Camera setup ---

    start_x = (scene_width - 80) // 2 * 10
    pyunicodegame.set_camera(x=start_x, y=0, mode="perspective", depth_scale=0.1)
    camera_speed = 80

    def update(dt):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * camera_speed * dt
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * camera_speed * dt
        if dx or dy:
            pyunicodegame.move_camera(dx, dy)

    def on_key(key):
        if key == pygame.K_p:
            _, _, mode, _ = pyunicodegame.get_camera()
            pyunicodegame.set_camera(mode="orthographic" if mode == "perspective" else "perspective")
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        cx, cy, mode, _ = pyunicodegame.get_camera()

        ui.put_string(2, 0, "CAMERA DEMO - Parallax Scrolling", (200, 200, 255))
        ui.put_string(2, 1, "Arrow keys: Move   P: Toggle mode   Q: Quit", (150, 150, 150))
        ui.put_string(2, 2, f"Cam: ({cx:.0f},{cy:.0f}) {mode.upper()}", (100, 100, 100))

        fps = pyunicodegame._clock.get_fps()
        ui.put_string(80 - 8, 0, f"FPS:{fps:.0f}", (100, 100, 100))

    pyunicodegame.run(update=update, render=render, on_key=on_key)


if __name__ == "__main__":
    main()
