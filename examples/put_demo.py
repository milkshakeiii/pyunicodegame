#!/usr/bin/env python3
"""
Put demo - nighttime road with palm trees and starry sky.

Demonstrates using put() for manual character-by-character rendering:
- Window.put(x, y, char, fg, bg) for drawing individual characters
- Multiple windows with different z-indexes and font sizes
- Manual scrolling and animation without sprites
- Drawing complex shapes (moon, palm trees) with put() calls
"""

import math
import random
import pygame
import pyunicodegame


class Scene:
    def __init__(self):
        self.scroll_x = 0.0
        self.stars = []
        self.palm_trees = []

    def init(self):
        """Initialize stars and palm trees."""
        sky = pyunicodegame.get_window("sky")
        for _ in range(80):
            x = random.randint(0, sky.width - 1)
            y = random.randint(0, sky.height - 15)
            brightness = random.randint(150, 255)
            twinkle_speed = random.uniform(1.0, 3.0)
            self.stars.append({
                "x": x, "y": y,
                "brightness": brightness,
                "twinkle": twinkle_speed,
                "phase": random.uniform(0, 6.28)
            })

        road = pyunicodegame.get_window("road")
        for i in range(10):
            x = i * 18 + random.randint(-3, 3)
            self.palm_trees.append({"x": x})

    def update(self, dt):
        self.scroll_x += dt * 4

        for star in self.stars:
            star["phase"] += dt * star["twinkle"]

    def render(self):
        self._render_sky()
        self._render_road()

    def _render_sky(self):
        sky = pyunicodegame.get_window("sky")
        sky_offset = int(self.scroll_x / 4) % sky.width

        # Stars
        for star in self.stars:
            x = (star["x"] - sky_offset) % sky.width
            twinkle = int(star["brightness"] * (0.7 + 0.3 * math.sin(star["phase"])))
            twinkle = max(0, min(255, twinkle))
            char = "*" if twinkle > 200 else "."
            if random.random() < 0.01:
                char = random.choice([".", "*", "+"])
            blue = min(255, twinkle + 20)
            sky.put(x, star["y"], char, (twinkle, twinkle, blue))

        # Moon (bigger, scrolls with stars)
        moon_x = (sky.width - 12 - sky_offset) % sky.width
        moon_color = (255, 255, 200)
        # Top row
        sky.put(moon_x + 1, 1, "_", moon_color)
        sky.put(moon_x + 2, 1, "_", moon_color)
        # Middle rows
        sky.put(moon_x, 2, "(", moon_color)
        sky.put(moon_x + 1, 2, " ", moon_color)
        sky.put(moon_x + 2, 2, " ", moon_color)
        sky.put(moon_x + 3, 2, ")", moon_color)
        sky.put(moon_x, 3, "(", moon_color)
        sky.put(moon_x + 1, 3, "_", moon_color)
        sky.put(moon_x + 2, 3, "_", moon_color)
        sky.put(moon_x + 3, 3, ")", moon_color)

    def _render_road(self):
        road = pyunicodegame.get_window("road")
        road_offset = int(self.scroll_x) % road.width

        road_top = 23
        road_bottom = 28

        # Road surface
        for y in range(road_top, road_bottom + 1):
            for x in range(road.width):
                road.put(x, y, " ", bg=(30, 30, 35))

        # Road edges
        for x in range(road.width):
            road.put(x, road_top, "═", (60, 60, 60))
            road.put(x, road_bottom, "═", (60, 60, 60))

        # Center dashes
        center_y = (road_top + road_bottom) // 2
        for x in range(road.width):
            dash_offset = (x + int(self.scroll_x)) % 8
            if dash_offset < 4:
                road.put(x, center_y, "─", (200, 200, 50))

        # Ground strip
        for y in range(road_top - 3, road_top):
            for x in range(road.width):
                road.put(x, y, " ", bg=(15, 25, 15))

        # Palm trees
        for tree in self.palm_trees:
            self._draw_palm_tree(road, tree["x"], road_top, road_offset)

    def _draw_palm_tree(self, window, base_x, road_top, offset):
        """Draw a thick palm tree silhouette."""
        x = (base_x - offset) % window.width

        trunk_color = (30, 60, 30)
        frond_color = (20, 80, 35)

        ground_y = road_top - 1

        # Solid trunk (1 char wide)
        for dy in range(1, 6):
            window.put(x, ground_y - dy, "█", trunk_color)

        # Fronds - fuller canopy
        top_y = ground_y - 6
        # Center mass
        window.put(x, top_y, "█", frond_color)
        window.put(x - 1, top_y, "▓", frond_color)
        window.put(x + 1, top_y, "▓", frond_color)
        # Drooping fronds
        window.put(x - 2, top_y + 1, "\\", frond_color)
        window.put(x - 3, top_y + 2, "\\", frond_color)
        window.put(x + 2, top_y + 1, "/", frond_color)
        window.put(x + 3, top_y + 2, "/", frond_color)
        # Top fronds
        window.put(x - 1, top_y - 1, "/", frond_color)
        window.put(x + 1, top_y - 1, "\\", frond_color)
        window.put(x, top_y - 1, "▀", frond_color)


def main():
    pyunicodegame.init("Put Demo - Night Drive", width=80, height=30, bg=(5, 5, 15, 255))

    pyunicodegame.create_window(
        "sky", x=0, y=0, width=134, height=47,
        z_index=0, font_name="6x13",
        alpha=255, bg=(5, 5, 20, 255)
    )

    pyunicodegame.create_window(
        "road", x=0, y=0, width=80, height=30,
        z_index=10, font_name="10x20",
        alpha=255, bg=(0, 0, 0, 0)
    )

    scene = Scene()
    scene.init()

    def on_key(key):
        if key == pygame.K_q:
            pyunicodegame.quit()

    pyunicodegame.run(update=scene.update, render=scene.render, on_key=on_key)


if __name__ == "__main__":
    main()
