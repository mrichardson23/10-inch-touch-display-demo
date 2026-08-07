import os
import sys
import json
import time
import subprocess

# Set SDL hints before importing/initializing Pygame
os.environ["SDL_HINT_TOUCH_MOUSE_EVENTS"] = "0"
os.environ["SDL_HINT_MOUSE_TOUCH_EVENTS"] = "0"
os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
os.environ["WAYLAND_DISPLAY"] = "wayland-0"

import pygame
from assets import AssetManager
from input_manager import InputManager
from effects import EffectEngine
from admin_server import AdminServer, get_config_paths
from admin_gui import AdminGuiModal

last_admin_launch = 0.0

def load_config():
    user_cfg_path, app_cfg_path = get_config_paths()
    default_config = {
        "header_title": "Raspberry Pi's new 10-inch Touch Display 2",
        "header_subtitle": "1200×1920 • 10-Point Multi-Touch Capacitive Display",
        "idle_cta_text": "TOUCH THE SCREEN WITH UP TO 10 FINGERS",
        "hud_touch_label": "TOUCH POINTS",
        "hud_mode_idle_text": "MODE: DEMO IDLE",
        "hud_mode_interactive_text": "MODE: MULTI-TOUCH INTERACTIVE",
        "touch_badge_label": "FINGER #{slot} ({x}, {y})",
        "primary_logo": "MFH.png",
        "active_logos": ["MFH.png", "logo.png"],
        "logo_scales": {"MFH.png": 1.0, "logo.png": 1.0},
        "idle_timeout_seconds": 4.0,
        "admin_port": 8080
    }
    if os.path.exists(app_cfg_path):
        try:
            with open(app_cfg_path, "r") as f:
                default_config.update(json.load(f))
        except Exception:
            pass

    if os.path.exists(user_cfg_path):
        try:
            with open(user_cfg_path, "r") as f:
                default_config.update(json.load(f))
        except Exception:
            pass

    return default_config

def save_config_persistent(new_config):
    user_cfg_path, app_cfg_path = get_config_paths()
    try:
        os.makedirs(os.path.dirname(user_cfg_path), exist_ok=True)
        with open(user_cfg_path, "w") as f:
            json.dump(new_config, f, indent=2)
    except Exception as e:
        print(f"[Main] Error writing user config: {e}")

    try:
        with open(app_cfg_path, "w") as f:
            json.dump(new_config, f, indent=2)
    except Exception as e:
        print(f"[Main] Error writing app config: {e}")

def main():
    print("[Main] Starting Raspberry Pi 10-Inch Touch Display 2 Native Demo...")

    WIDTH, HEIGHT = 1200, 1920

    pygame.init()
    pygame.mouse.set_visible(False)

    flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    except Exception:
        print("[Main] Fullscreen mode fallback to standard surface")
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.display.set_caption("Raspberry Pi 10-Inch Touch Display 2 Demo")

    assets = AssetManager(WIDTH, HEIGHT)
    assets.init()

    effects = EffectEngine(assets, WIDTH, HEIGHT)
    config = load_config()
    admin_port = config.get("admin_port", 8080)

    running = True

    def on_gui_save(updated_config):
        nonlocal config
        config = updated_config
        save_config_persistent(config)
        print("[Main] Saved config from native on-screen Admin GUI Modal!")

    admin_gui = AdminGuiModal(assets, WIDTH, HEIGHT, save_callback=on_gui_save)

    def on_minimize():
        print("[Main] ESC pressed — Minimizing demo to taskbar...")
        try:
            pygame.display.iconify()
        except Exception as e:
            print(f"[Main] Minimize note: {e}")

    def on_admin_key():
        try:
            effects.trigger_admin_toast()
            admin_gui.toggle(config, assets.get_available_image_files())
        except Exception as e:
            print(f"[Main] Error in on_admin_key: {e}")

    input_mgr = InputManager(WIDTH, HEIGHT, admin_key_callback=on_admin_key, minimize_callback=on_minimize)

    admin_server = AdminServer(port=admin_port)
    admin_server.start()

    clock = pygame.time.Clock()
    last_config_check = time.time()
    last_touch_time = time.time()
    last_frame_time = time.time()

    print(f"[Main] Native Demo running at {WIDTH}x{HEIGHT} 60 FPS! Press 'TAB', 'F1', 'A', or 'C' to toggle Native Admin GUI Modal.")

    while running:
        current_time = time.time()
        dt = current_time - last_frame_time
        last_frame_time = current_time

        # 1. Hot reload config every 1 second
        if current_time - last_config_check > 1.0:
            config = load_config()
            last_config_check = current_time

        # 2. Hardware multi-touch active points
        active_touches = input_mgr.get_active_touches()
        num_touches = len(active_touches)

        # 3. Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Modal captures mouse and keyboard SDL events when open
            if admin_gui.is_open:
                if admin_gui.handle_event(event):
                    continue

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    on_minimize()
                elif event.key in [pygame.K_TAB, pygame.K_F1, pygame.K_a, pygame.K_c]:
                    on_admin_key()
            else:
                input_mgr.handle_sdl_event(event)

        # 4. Touch effects & Idle state update (Only when Admin Modal is CLOSED)
        if admin_gui.is_open:
            # Route touches to Admin Modal exclusively, freeze background demo
            admin_gui.update_touch_inputs(active_touches)
            effects.update(dt, True, 0)
        else:
            if num_touches > 0:
                last_touch_time = current_time
                for touch in active_touches:
                    effects.spawn_touch_effects(touch, num_touches)

            idle_timeout = config.get("idle_timeout_seconds", 4.0)
            is_idle = (current_time - last_touch_time) > idle_timeout
            effects.update(dt, is_idle, num_touches)

        idle_timeout = config.get("idle_timeout_seconds", 4.0)
        is_idle = (current_time - last_touch_time) > idle_timeout

        # 5. Render Scene
        effects.draw_background(screen)

        if is_idle or admin_gui.is_open:
            effects.draw_idle_mode(screen, config)
        else:
            effects.draw_interactive_mode(screen, active_touches, config)

        # Header overlay & HUD status bar
        effects.draw_header_overlay(
            screen,
            config,
            0 if admin_gui.is_open else num_touches,
            clock.get_fps(),
            is_idle or admin_gui.is_open
        )

        # Render Native Admin GUI Modal if open
        if admin_gui.is_open:
            admin_gui.draw(screen)

        # 6. Flip display buffer
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
