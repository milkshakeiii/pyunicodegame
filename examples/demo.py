#!/usr/bin/env python3
"""
Demo script for pyunicodegame library.

This demonstrates the main features:
- Basic grid rendering
- Panels and borders
- Glow effects
- Particle systems
- Animations
- Fullscreen with aspect ratio preservation (Alt+Enter / Option+Enter)
"""

import pygame
import pyunicodegame as pug


def toggle_fullscreen(screen, base_width, base_height):
    """Toggle between windowed and fullscreen mode."""
    is_fullscreen = screen.get_flags() & pygame.FULLSCREEN
    if is_fullscreen:
        return pygame.display.set_mode((base_width, base_height))
    else:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)


def render_scaled(screen, render_surface, base_width, base_height):
    """Render surface to screen with aspect ratio preservation."""
    screen_w, screen_h = screen.get_size()

    # If screen matches render surface, just blit directly
    if screen_w == base_width and screen_h == base_height:
        screen.blit(render_surface, (0, 0))
        return

    # Calculate scale factor maintaining aspect ratio
    scale_x = screen_w / base_width
    scale_y = screen_h / base_height
    scale = min(scale_x, scale_y)

    # Calculate scaled dimensions and offset for centering
    scaled_w = int(base_width * scale)
    scaled_h = int(base_height * scale)
    offset_x = (screen_w - scaled_w) // 2
    offset_y = (screen_h - scaled_h) // 2

    # Fill with black for letterbox/pillarbox bars
    screen.fill((0, 0, 0))

    # Scale and blit
    scaled = pygame.transform.scale(render_surface, (scaled_w, scaled_h))
    screen.blit(scaled, (offset_x, offset_y))


def main():
    pygame.init()

    # Create renderer with Cogmind theme
    renderer = pug.Renderer(
        width=80,
        height=30,
        scale=1,
        theme=pug.CogmindTheme(),
        enable_bloom=True
    )

    # Base dimensions for the render surface
    base_width = renderer.pixel_width
    base_height = renderer.pixel_height

    # Create window at native size
    screen = pygame.display.set_mode((base_width, base_height))
    pygame.display.set_caption("pyunicodegame Demo")
    clock = pygame.time.Clock()

    # Create a fixed-size render surface
    render_surface = pygame.Surface((base_width, base_height))

    # Create a spinner animation
    spinner = pug.FrameAnimation(frames=["|", "/", "-", "\\"], fps=8)

    # Player position
    player_x, player_y = 40, 15

    # Track fullscreen state
    is_fullscreen = False

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Alt+Enter or Option+Enter to toggle fullscreen
                if event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                    screen = toggle_fullscreen(screen, base_width, base_height)
                    is_fullscreen = not is_fullscreen
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    player_y = max(1, player_y - 1)
                elif event.key == pygame.K_DOWN:
                    player_y = min(renderer.height - 2, player_y + 1)
                elif event.key == pygame.K_LEFT:
                    player_x = max(1, player_x - 1)
                elif event.key == pygame.K_RIGHT:
                    player_x = min(renderer.width - 2, player_x + 1)
                elif event.key == pygame.K_SPACE:
                    # Spawn explosion at player position
                    renderer.spawn_particles(pug.explosion(player_x, player_y))
                elif event.key == pygame.K_s:
                    # Spawn sparks
                    renderer.spawn_particles(pug.sparks(player_x, player_y, (0, -1)))
                elif event.key == pygame.K_m:
                    # Spawn magic sparkle
                    renderer.spawn_particles(pug.magic_sparkle(player_x, player_y))

        # Update spinner
        spinner.update(dt)

        # Clear screen with theme background
        renderer.clear()

        # Draw border around screen
        renderer.draw_box(0, 0, renderer.width, renderer.height, pug.BorderStyle.double())

        # Draw status panel
        renderer.draw_panel(1, 1, 25, 8, title="Status")
        renderer.put_string(2, 2, f"Pos: ({player_x}, {player_y})", fg=(200, 200, 200))
        renderer.put_string(2, 3, f"FPS: {int(clock.get_fps())}", fg=(200, 200, 200))
        renderer.put_string(2, 4, f"Spinner: {spinner.current_frame}", fg=(100, 200, 255))
        renderer.put_string(2, 5, f"Fullscreen: {is_fullscreen}", fg=(150, 150, 150))

        # Draw controls panel
        renderer.draw_panel(1, 9, 25, 10, title="Controls")
        renderer.put_string(2, 10, "Arrows: Move", fg=(150, 150, 150))
        renderer.put_string(2, 11, "Space: Explosion", fg=(150, 150, 150))
        renderer.put_string(2, 12, "S: Sparks", fg=(150, 150, 150))
        renderer.put_string(2, 13, "M: Magic", fg=(150, 150, 150))
        renderer.put_string(2, 14, "Alt+Enter: Fullscreen", fg=(150, 150, 150))
        renderer.put_string(2, 15, "Esc: Quit", fg=(150, 150, 150))

        # Draw glowing elements with varying intensities
        renderer.put_string(30, 3, "Glow intensity:", fg=(100, 100, 100))
        intensities = [0.2, 0.4, 0.6, 0.8, 1.0]
        for i, intensity in enumerate(intensities):
            x = 30 + i * 5
            renderer.put(x, 5, "*", fg=(255, 150, 50), glow=intensity)
            label = f"{intensity:.1f}"
            renderer.put_string(x - 1, 7, label, fg=(80, 80, 80))

        # Draw some colored glowing objects
        renderer.put(50, 10, "#", fg=(255, 50, 50), glow=0.7)    # Red
        renderer.put(54, 10, "#", fg=(50, 255, 50), glow=0.7)    # Green
        renderer.put(58, 10, "#", fg=(50, 150, 255), glow=0.7)   # Blue
        renderer.put(62, 10, "#", fg=(255, 255, 100), glow=0.7)  # Yellow
        renderer.put(66, 10, "#", fg=(255, 100, 255), glow=0.7)  # Magenta

        # Draw player with glow
        renderer.put(player_x, player_y, "@", fg=(0, 255, 0), glow=0.6)

        # Update animations and particles
        renderer.update(dt)

        # Render to fixed-size surface first
        render_surface.fill((0, 0, 0))
        renderer.render(render_surface)

        # Then scale to screen with aspect ratio preservation
        render_scaled(screen, render_surface, base_width, base_height)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
