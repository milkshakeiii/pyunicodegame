#!/usr/bin/env python3
"""
Demo of the bloom post-processing effect.

Shows how bright pixels glow and how emissive sprites bypass the threshold.
Controls: B toggle, T/Y threshold, U/I blur_scale, O/P intensity, Q quit.
"""

import pygame
import pyunicodegame


def main():
    root = pyunicodegame.init("Bloom Demo", width=80, height=25, bg=(5, 5, 15, 255))

    # Bloom parameters
    bloom_enabled = True
    threshold = 180
    blur_scale = 4
    intensity = 1.0

    def update_bloom():
        root.set_bloom(enabled=bloom_enabled, threshold=threshold,
                       blur_scale=blur_scale, intensity=intensity)

    update_bloom()

    # Create some sprites to demonstrate emissive property
    # Bright sprite (will glow due to high brightness)
    bright_star = pyunicodegame.create_sprite("*", x=20, y=8, fg=(255, 255, 200))
    root.add_sprite(bright_star)

    # Dim sprite marked as emissive (will glow despite low brightness)
    emissive_orb = pyunicodegame.create_sprite("O", x=40, y=8, fg=(100, 100, 200), emissive=True)
    root.add_sprite(emissive_orb)

    # Dim sprite NOT emissive (won't glow)
    dim_dot = pyunicodegame.create_sprite(".", x=60, y=8, fg=(100, 100, 100))
    root.add_sprite(dim_dot)

    # Create a fire emitter with emissive particles
    fire = pyunicodegame.create_emitter(
        x=40, y=20,
        chars="*+.",
        colors=[(255, 200, 50), (255, 150, 30), (255, 100, 0)],
        spawn_rate=12,
        spread=(1.0, 0.2),
        speed=4, speed_variance=0.3,
        direction=90, arc=40,
        drag=0.4,
        fade_time=1.0, fade_time_variance=0.3,
        emitter_duration=0,  # Infinite
    )
    root.add_emitter(fire)

    def on_key(key):
        nonlocal bloom_enabled, threshold, blur_scale, intensity
        if key == pygame.K_b:
            bloom_enabled = not bloom_enabled
            update_bloom()
        # Threshold: T/Y
        elif key == pygame.K_t:
            threshold = max(0, threshold - 10)
            update_bloom()
        elif key == pygame.K_y:
            threshold = min(255, threshold + 10)
            update_bloom()
        # Blur scale: U/I
        elif key == pygame.K_u:
            blur_scale = max(1, blur_scale - 1)
            update_bloom()
        elif key == pygame.K_i:
            blur_scale += 1
            update_bloom()
        # Intensity: O/P
        elif key == pygame.K_o:
            intensity = max(0.0, intensity - 0.1)
            update_bloom()
        elif key == pygame.K_p:
            intensity += 0.1
            update_bloom()
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Title
        root.put_string(2, 1, "BLOOM EFFECT DEMO", (200, 200, 255))

        # Controls
        root.put_string(2, 3, "B: toggle   T/Y: threshold   U/I: blur   O/P: intensity   Q: quit", (100, 100, 100))

        # Status - show all parameters
        status = f"Bloom: {'ON' if bloom_enabled else 'OFF'}"
        root.put_string(2, 5, status, (150, 150, 150))
        root.put_string(2, 6, f"Threshold: {threshold}", (150, 150, 150))
        root.put_string(22, 6, f"Blur: {blur_scale}", (150, 150, 150))
        root.put_string(35, 6, f"Intensity: {intensity:.1f}", (150, 150, 150))

        # Labels for sprites
        root.put_string(15, 10, "Bright (255,255,200)", (80, 80, 80))
        root.put_string(15, 11, "Glows naturally", (60, 60, 60))

        root.put_string(35, 10, "Dim + Emissive", (80, 80, 80))
        root.put_string(35, 11, "Bypasses threshold", (60, 60, 60))

        root.put_string(55, 10, "Dim (100,100,100)", (80, 80, 80))
        root.put_string(55, 11, "No glow", (60, 60, 60))

        # Fire label
        root.put_string(36, 22, "Fire Effect", (80, 80, 80))

        # Draw some bright text that will glow
        root.put_string(30, 15, "GLOWING TEXT", (255, 255, 150))

        # Draw dim text that won't glow
        root.put_string(30, 17, "normal text", (80, 80, 80))

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
