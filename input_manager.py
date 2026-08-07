import os
import time
import threading
import pygame

# 10 vibrant distinct colors for 10 fingers
FINGER_COLORS = [
    (255, 45, 85),     # 0: Neon Red / Hot Pink
    (57, 255, 20),     # 1: Electric Lime
    (0, 245, 255),     # 2: Vivid Cyan
    (255, 215, 0),     # 3: Electric Gold
    (175, 82, 222),    # 4: Neon Purple
    (255, 149, 0),     # 5: Bright Orange
    (0, 122, 255),     # 6: Electric Blue
    (255, 0, 200),     # 7: Magenta
    (0, 250, 154),     # 8: Mint Green
    (255, 235, 59)      # 9: Bright Yellow
]

class TouchPoint:
    def __init__(self, finger_id, slot, x, y):
        self.finger_id = finger_id
        self.slot = slot
        self.x = x
        self.y = y
        self.prev_x = x
        self.prev_y = y
        self.dx = 0.0
        self.dy = 0.0
        self.active = True
        self.start_time = time.time()
        self.last_update = time.time()
        self.color = FINGER_COLORS[slot % len(FINGER_COLORS)]

    def update(self, x, y):
        self.prev_x = self.x
        self.prev_y = self.y
        self.dx = x - self.prev_x
        self.dy = y - self.prev_y
        self.x = x
        self.y = y
        self.last_update = time.time()

class InputManager:
    def __init__(self, screen_w=1200, screen_h=1920, admin_key_callback=None, minimize_callback=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.lock = threading.Lock()
        self.admin_key_callback = admin_key_callback
        self.minimize_callback = minimize_callback
        self.active_slots = {}
        self.mouse_sim_id = "mouse_sim"
        self.mouse_active = False

        self.start_evdev_touch_reader()
        self.start_evdev_keyboard_reader()

    def start_evdev_touch_reader(self):
        """Read Linux multi-touch Type B events directly from /dev/input device."""
        def touch_thread():
            try:
                import evdev
                from evdev import ecodes

                touch_dev = None
                for path in evdev.list_devices():
                    try:
                        dev = evdev.InputDevice(path)
                        caps = dev.capabilities()
                        if ecodes.EV_ABS in caps:
                            abs_codes = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                            if ecodes.ABS_MT_POSITION_X in abs_codes or ecodes.ABS_MT_SLOT in abs_codes:
                                touch_dev = dev
                                print(f"[InputManager] Found Hardware Multi-Touch Device: {dev.name} ({dev.path})")
                                break
                    except Exception:
                        continue

                if not touch_dev:
                    return

                current_slot = 0
                temp_slots = {}

                for event in touch_dev.read_loop():
                    if event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_MT_SLOT:
                            current_slot = event.value
                            if current_slot not in temp_slots:
                                temp_slots[current_slot] = {'x': 0, 'y': 0, 'tracking_id': -1, 'active': False}

                        elif event.code == ecodes.ABS_MT_TRACKING_ID:
                            if current_slot not in temp_slots:
                                temp_slots[current_slot] = {'x': 0, 'y': 0, 'tracking_id': -1, 'active': False}
                            if event.value != -1:
                                temp_slots[current_slot]['tracking_id'] = event.value
                                temp_slots[current_slot]['active'] = True
                            else:
                                temp_slots[current_slot]['tracking_id'] = -1
                                temp_slots[current_slot]['active'] = False

                        elif event.code == ecodes.ABS_MT_POSITION_X:
                            if current_slot not in temp_slots:
                                temp_slots[current_slot] = {'x': 0, 'y': 0, 'tracking_id': -1, 'active': False}
                            temp_slots[current_slot]['x'] = event.value

                        elif event.code == ecodes.ABS_MT_POSITION_Y:
                            if current_slot not in temp_slots:
                                temp_slots[current_slot] = {'x': 0, 'y': 0, 'tracking_id': -1, 'active': False}
                            temp_slots[current_slot]['y'] = event.value

                    elif event.type == ecodes.EV_SYN and event.code == ecodes.SYN_REPORT:
                        with self.lock:
                            for slot_idx, sdata in temp_slots.items():
                                if sdata['active']:
                                    px = max(0, min(self.screen_w, sdata['x']))
                                    py = max(0, min(self.screen_h, sdata['y']))
                                    if slot_idx in self.active_slots:
                                        self.active_slots[slot_idx].update(px, py)
                                    else:
                                        self.active_slots[slot_idx] = TouchPoint(sdata['tracking_id'], slot_idx, px, py)
                                else:
                                    if slot_idx in self.active_slots:
                                        del self.active_slots[slot_idx]

            except Exception as e:
                print(f"[InputManager] evdev touch reader error: {e}")

        t = threading.Thread(target=touch_thread, daemon=True)
        t.start()

    def start_evdev_keyboard_reader(self):
        """Read hardware keyboard key events directly from /dev/input for TAB, F1, A, C, ESC."""
        def kbd_thread():
            try:
                import evdev
                from evdev import ecodes

                kbd_devices = []
                for path in evdev.list_devices():
                    try:
                        dev = evdev.InputDevice(path)
                        caps = dev.capabilities()
                        if ecodes.EV_KEY in caps:
                            kbd_devices.append(dev)
                            print(f"[InputManager] Hooked Hardware Keyboard: {dev.name} ({dev.path})")
                    except Exception:
                        continue

                for kbd in kbd_devices:
                    def listen_device(dev):
                        for event in dev.read_loop():
                            if event.type == ecodes.EV_KEY and event.value == 1: # Key down
                                if event.code in [ecodes.KEY_TAB, ecodes.KEY_F1, ecodes.KEY_A, ecodes.KEY_C]:
                                    print(f"[InputManager] Admin shortcut key pressed on keyboard ({event.code})")
                                    if self.admin_key_callback:
                                        try:
                                            self.admin_key_callback()
                                        except Exception as e:
                                            print(f"[InputManager] Error in admin_key_callback: {e}")

                                elif event.code in [ecodes.KEY_ESC, ecodes.KEY_Q]:
                                    print(f"[InputManager] Minimize key pressed on keyboard ({event.code})")
                                    if self.minimize_callback:
                                        try:
                                            self.minimize_callback()
                                        except Exception as e:
                                            print(f"[InputManager] Error in minimize_callback: {e}")

                    threading.Thread(target=listen_device, args=(kbd,), daemon=True).start()

            except Exception as e:
                print(f"[InputManager] evdev kbd reader note: {e}")

        t = threading.Thread(target=kbd_thread, daemon=True)
        t.start()

    def handle_sdl_event(self, event):
        """Process Pygame SDL mouse and keyboard events safely."""
        with self.lock:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                    if self.minimize_callback:
                        self.minimize_callback()
                elif event.key in [pygame.K_TAB, pygame.K_F1, pygame.K_a, pygame.K_c]:
                    if self.admin_key_callback:
                        try:
                            self.admin_key_callback()
                        except Exception as e:
                            print(f"[InputManager] Error in admin_key_callback: {e}")

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if len(self.active_slots) == 0 or self.mouse_sim_id in [tp.finger_id for tp in self.active_slots.values()]:
                    px, py = event.pos
                    slot = 0
                    tp = TouchPoint(self.mouse_sim_id, slot, px, py)
                    self.active_slots[slot] = tp
                    self.mouse_active = True

            elif event.type == pygame.MOUSEMOTION and self.mouse_active:
                px, py = event.pos
                if 0 in self.active_slots:
                    self.active_slots[0].update(px, py)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if 0 in self.active_slots:
                    del self.active_slots[0]
                self.mouse_active = False

    def get_active_touches(self):
        """Return list of active TouchPoint objects sorted by slot."""
        with self.lock:
            return sorted(list(self.active_slots.values()), key=lambda t: t.slot)
