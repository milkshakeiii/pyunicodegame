#!/usr/bin/env python3
"""
Demo of the EffectSpriteEmitter system.

Shows various particle effects created with different emitter configurations.
Press SPACE to respawn all emitters.
"""

import pygame
import pyunicodegame


def create_all_emitters(root):
    """Create and add all demo emitters to the window."""
    emitters = []

    # 1. Fire - fast upward orange/yellow particles
    fire = pyunicodegame.create_emitter(
        x=8, y=22,
        chars="*+.",
        colors=[(255, 200, 50), (255, 150, 30), (255, 100, 0), (255, 50, 0)],
        spawn_rate=15,
        spawn_rate_variance=0.3,
        spread=(1.0, 0.2),
        speed=6, speed_variance=0.4,
        direction=90, arc=40,  # Upward cone
        drag=0.3,
        fade_time=0.8, fade_time_variance=0.3,
        emitter_duration=3.0,
    )
    emitters.append(("Fire", fire))

    # 2. Smoke - slow rising gray particles
    smoke = pyunicodegame.create_emitter(
        x=20, y=22,
        chars=".oO",
        colors=[(80, 80, 80), (100, 100, 100), (120, 120, 120), (140, 140, 140)],
        spawn_rate=4,
        spread=(0.5, 0.0),
        speed=1.5, speed_variance=0.2,
        direction=90, arc=25,  # Mostly straight up
        drag=0.8,
        fade_time=2.5, fade_time_variance=0.3,
        emitter_duration=4.0,
    )
    emitters.append(("Smoke", smoke))

    # 3. Sparks - directional welding-style sparks
    sparks = pyunicodegame.create_emitter(
        x=32, y=15,
        chars="*.",
        colors=[(255, 255, 100), (255, 200, 50), (255, 255, 200)],
        spawn_rate=20,
        spawn_rate_variance=0.5,
        speed=8, speed_variance=0.5,
        direction=45, arc=30,  # Diagonal up-right
        drag=0.2,
        fade_time=0.4, fade_time_variance=0.3,
        emitter_duration=2.5,
    )
    emitters.append(("Sparks", sparks))

    # 4. Magic sparkle - cell-locked, slow, colorful
    magic = pyunicodegame.create_emitter(
        x=44, y=12,
        chars="*+.",
        colors=[(150, 100, 255), (100, 150, 255), (200, 100, 255), (255, 255, 255)],
        spawn_rate=8,
        spread=(2.0, 2.0),
        cell_locked=True,  # Snap to cell centers
        speed=0.5, speed_variance=0.5,
        direction=90, arc=360,  # Omnidirectional
        drag=0.5,
        fade_time=1.2, fade_time_variance=0.4,
        emitter_duration=4.0,
    )
    emitters.append(("Magic", magic))

    # 5. Fountain - upward burst that spreads and falls
    fountain = pyunicodegame.create_emitter(
        x=56, y=20,
        chars=".",
        colors=[(100, 150, 255), (150, 200, 255), (200, 230, 255)],
        spawn_rate=25,
        spread=(0.3, 0.0),
        speed=10, speed_variance=0.3,
        direction=90, arc=20,  # Tight upward cone
        drag=0.15,  # Slows down quickly
        fade_time=1.5,
        emitter_duration=3.0,
    )
    emitters.append(("Fountain", fountain))

    # 6. Rain - downward streaks
    rain = pyunicodegame.create_emitter(
        x=68, y=2,
        chars="|'",
        colors=[(100, 150, 200), (120, 170, 220)],
        spawn_rate=12,
        spread=(3.0, 0.0),
        speed=15, speed_variance=0.2,
        direction=270, arc=10,  # Downward
        drag=1.0,  # No drag
        fade_time=0.0,  # No fade
        duration=1.2, duration_variance=0.2,  # Hard cutoff
        emitter_duration=4.0,
    )
    emitters.append(("Rain", rain))

    # 7. Explosion - short burst in all directions
    explosion = pyunicodegame.create_emitter(
        x=10, y=8,
        chars="*#@%+",
        colors=[(255, 255, 100), (255, 200, 50), (255, 150, 0), (255, 100, 0), (255, 50, 0)],
        spawn_rate=200,  # Lots of particles very quickly
        speed=12, speed_variance=0.5,
        direction=0, arc=360,  # All directions
        drag=0.15,
        fade_time=0.6, fade_time_variance=0.3,
        emitter_duration=0.15,  # Very short burst
    )
    emitters.append(("Explosion", explosion))

    # Add all emitters to window
    for name, emitter in emitters:
        root.add_emitter(emitter)

    return emitters


def main():
    root = pyunicodegame.init("Emitter Demo", width=80, height=25, bg=(10, 10, 20, 255))

    emitters = create_all_emitters(root)

    def on_key(key):
        nonlocal emitters
        if key == pygame.K_SPACE:
            # Kill existing emitters and respawn
            for name, emitter in emitters:
                emitter.kill()
            emitters = create_all_emitters(root)
        elif key == pygame.K_q:
            pyunicodegame.quit()

    def render():
        # Draw labels for each effect
        labels = [
            (8, 24, "Fire"),
            (20, 24, "Smoke"),
            (32, 17, "Sparks"),
            (44, 16, "Magic"),
            (56, 22, "Fountain"),
            (68, 8, "Rain"),
            (10, 14, "Explosion"),
        ]
        for x, y, label in labels:
            root.put_string(x - len(label) // 2, y, label, (80, 80, 80))

        # Instructions
        root.put_string(1, 1, "SPACE: respawn emitters   Q: quit", (100, 100, 100))

        # Show active emitter and particle count (bottom-middle)
        active = sum(1 for name, e in emitters if e.alive)
        status = f"Emitters: {active}/{len(emitters)}  Particles: {len(root._sprites)}"
        root.put_string(40 - len(status) // 2, 23, status, (80, 80, 80))

    pyunicodegame.run(render=render, on_key=on_key)


if __name__ == "__main__":
    main()
