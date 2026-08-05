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

def open_admin_browser(port=8080):
    """Launch Admin Web Control Panel in Chromium browser on Pi desktop."""
    global last_admin_launch
    now = time.time()
    if now - last_admin_launch < 1.0: # 1-second debounce
        return
    last_admin_launch = now

    try:
        url = f"http://localhost:{port}"
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        env["WAYLAND_DISPLAY"] = "wayland-0"
        env["XDG_RUNTIME_DIR"] = "/run/user/1000"

        try:
            pygame.display.iconify()
        except Exception as e:
            print(f"[Main] Pygame iconify note: {e}")

        cmd = [
            "/usr/bin/chromium",
            "--new-window",
            url
        ]
        subprocess.Popen(cmd, env=env)
        print(f"[Main] Launched Chromium new window for {url}")
    except Exception as e:
        print(f"[Main] Error launching admin browser: {e}")

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

    # Callback when Admin key ('TAB', 'F1', 'A') is pressed in Pygame focus
    def on_admin_key():
        try:
            effects.trigger_admin_toast()
            open_admin_browser(admin_port)
        except Exception as e:
            print(f"[Main] Error in on_admin_key: {e}")

    input_mgr = InputManager(WIDTH, HEIGHT, admin_key_callback=on_admin_key)

    admin_server = AdminServer(port=admin_port)
    admin_server.start()

    clock = pygame.time.Clock()
    last_config_check = time.time()
    last_touch_time = time.time()
    last_frame_time = time.time()

    running = True
    print(f"[Main] Native Demo running at {WIDTH}x{HEIGHT} 60 FPS! Press 'TAB', 'F1', or 'A' key to open Admin Panel.")

    admin_keys = [pygame.K_TAB, pygame.K_F1, pygame.K_a]

    while running:
        current_time = time.time()
        dt = current_time - last_frame_time
        last_frame_time = current_time

        # 1. Hot reload config every 1 second
        if current_time - last_config_check > 1.0:
            config = load_config()
            last_config_check = current_time

        # 2. Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    running = False
                elif event.key in admin_keys:
                    on_admin_key()
            else:
                input_mgr.handle_sdl_event(event)

        # 3. Active touches & Idle state update
        active_touches = input_mgr.get_active_touches()
        num_touches = len(active_touches)

        if num_touches > 0:
            last_touch_time = current_time
            for touch in active_touches:
                effects.spawn_touch_effects(touch, num_touches)

        idle_timeout = config.get("idle_timeout_seconds", 4.0)
        is_idle = (current_time - last_touch_time) > idle_timeout

        # 4. Update effects engine
        effects.update(dt, is_idle, num_touches)

        # 5. Render Scene
        effects.draw_background(screen)

        if is_idle:
            effects.draw_idle_mode(screen, config)
        else:
            effects.draw_interactive_mode(screen, active_touches, config)

        # Header overlay & HUD status bar
        effects.draw_header_overlay(
            screen,
            config,
            num_touches,
            clock.get_fps(),
            is_idle
        )

        # 6. Flip display buffer
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
