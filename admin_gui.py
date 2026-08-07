import pygame
import os
import json
import time
import math

class AdminGuiModal:
    def __init__(self, assets, width=1200, height=1920, save_callback=None):
        self.assets = assets
        self.width = width
        self.height = height
        self.save_callback = save_callback
        self.is_open = False

        # Modal Dimensions
        self.modal_w = 920
        self.modal_h = 1480
        self.modal_x = (width - self.modal_w) // 2
        self.modal_y = (height - self.modal_h) // 2

        # State fields
        self.available_images = []
        self.config_data = {}
        self.active_text_field = None
        self.toast_message = ""
        self.toast_time = 0.0

        # Touch slider dragging state
        self.dragging_slider = None
        self.last_touch_handled = 0.0

    def open(self, config_data, available_images):
        self.config_data = json.loads(json.dumps(config_data)) # deep copy
        self.available_images = available_images
        self.active_text_field = None
        self.is_open = True
        try:
            pygame.mouse.set_visible(True)
        except Exception:
            pass
        print("[AdminGuiModal] Opened native on-screen Admin GUI Modal")

    def close(self):
        self.is_open = False
        self.active_text_field = None
        try:
            pygame.mouse.set_visible(False)
        except Exception:
            pass
        print("[AdminGuiModal] Closed native Admin GUI Modal")

    def toggle(self, config_data, available_images):
        if self.is_open:
            self.close()
        else:
            self.open(config_data, available_images)

    def trigger_toast(self, msg):
        self.toast_message = msg
        self.toast_time = time.time()

    def update_touch_inputs(self, active_touches):
        """Process direct hardware multi-touch finger taps & drags."""
        if not self.is_open or not active_touches:
            return

        now = time.time()
        for t in active_touches:
            tx, ty = int(t.x), int(t.y)
            pos = (tx, ty)

            # Handle slider dragging with touch
            if self.dragging_slider:
                self.update_slider_val(self.dragging_slider, self.dragging_slider_rect, pos)
                continue

            # Debounce tap processing
            if now - self.last_touch_handled > 0.22:
                if self.process_point_tap(pos):
                    self.last_touch_handled = now

    def process_point_tap(self, pos):
        """Unified point tap handler for both touch fingers and physical mouse clicks."""
        if not self.is_open:
            return False

        # 1. Close button (Top Right X)
        close_btn_rect = pygame.Rect(self.modal_x + self.modal_w - 60, self.modal_y + 20, 40, 40)
        if close_btn_rect.collidepoint(pos):
            self.close()
            return True

        # 2. Save & Cancel Footer Buttons
        save_btn_rect = pygame.Rect(self.modal_x + 40, self.modal_y + self.modal_h - 90, 400, 60)
        cancel_btn_rect = pygame.Rect(self.modal_x + 480, self.modal_y + self.modal_h - 90, 400, 60)

        if save_btn_rect.collidepoint(pos):
            if self.save_callback:
                self.save_callback(self.config_data)
            self.trigger_toast("SETTINGS SAVED & APPLIED!")
            self.close()
            return True

        if cancel_btn_rect.collidepoint(pos):
            self.close()
            return True

        # 3. Check UI Controls Collision
        if self.handle_ui_controls_tap(pos):
            return True

        self.active_text_field = None
        return False

    def handle_event(self, event):
        """Process physical mouse and keyboard SDL events."""
        if not self.is_open:
            return False

        # Physical Keyboard typing into active text field
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

            if self.active_text_field:
                if event.key == pygame.K_BACKSPACE:
                    self.config_data[self.active_text_field] = self.config_data.get(self.active_text_field, "")[:-1]
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    self.active_text_field = None
                elif event.unicode and event.unicode.isprintable():
                    self.config_data[self.active_text_field] = self.config_data.get(self.active_text_field, "") + event.unicode
                return True

        # Physical Mouse events
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.process_point_tap(event.pos)

        elif event.type == pygame.MOUSEMOTION and self.dragging_slider:
            self.update_slider_val(self.dragging_slider, self.dragging_slider_rect, event.pos)
            return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = None
            return True

        return True

    def update_slider_val(self, img, slider_rect, pos):
        rel_x = max(0, min(slider_rect.width, pos[0] - slider_rect.x))
        val = round(0.3 + (rel_x / slider_rect.width) * (2.5 - 0.3), 2)
        logo_scales = self.config_data.get("logo_scales", {})
        logo_scales[img] = val
        self.config_data["logo_scales"] = logo_scales

    def handle_ui_controls_tap(self, pos):
        """Check collision for radios, checkboxes, sliders, and text fields."""
        content_y = self.modal_y + 90
        
        # 1. Graphic Manager Items
        grid_x = self.modal_x + 40
        grid_y = content_y + 40

        for idx, img in enumerate(self.available_images):
            card_x = grid_x + (idx % 3) * 280
            card_y = grid_y + (idx // 3) * 220
            
            # Primary Radio Button
            radio_rect = pygame.Rect(card_x + 15, card_y + 115, 110, 32)
            if radio_rect.collidepoint(pos):
                self.config_data["primary_logo"] = img
                return True

            # Orbit Checkbox
            check_rect = pygame.Rect(card_x + 140, card_y + 115, 110, 32)
            if check_rect.collidepoint(pos):
                actives = self.config_data.get("active_logos", [])
                if img in actives:
                    if len(actives) > 1:
                        actives.remove(img)
                else:
                    actives.append(img)
                self.config_data["active_logos"] = actives
                return True

            # Scale Slider
            slider_rect = pygame.Rect(card_x + 15, card_y + 175, 230, 25)
            if slider_rect.collidepoint(pos):
                self.dragging_slider = img
                self.dragging_slider_rect = slider_rect
                self.update_slider_val(img, slider_rect, pos)
                return True

        # 2. Text Input Fields
        text_fields_y = grid_y + math.ceil(len(self.available_images) / 3.0) * 220 + 30
        fields = [
            ("header_title", "Top Header Title"),
            ("header_subtitle", "Top Header Subtitle"),
            ("idle_cta_text", "Idle CTA Button Text"),
            ("hud_touch_label", "HUD Touch Label"),
            ("hud_mode_idle_text", "HUD Idle Status"),
            ("hud_mode_interactive_text", "HUD Active Status"),
            ("touch_badge_label", "Finger Badge Format")
        ]

        for i, (key, label) in enumerate(fields):
            fy = text_fields_y + i * 55
            input_rect = pygame.Rect(self.modal_x + 300, fy, 570, 42)
            if input_rect.collidepoint(pos):
                self.active_text_field = key
                return True

        return False

    def draw(self, surface):
        """Render Glassmorphic Admin Modal and UI Controls cleanly without symbols/emojis."""
        if not self.is_open:
            return

        # Dimmed Background Blur Surface
        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((5, 8, 16, 200))
        surface.blit(dim_surf, (0, 0))

        # Main Modal Container
        modal_surf = pygame.Surface((self.modal_w, self.modal_h), pygame.SRCALPHA)
        pygame.draw.rect(modal_surf, (16, 24, 42, 245), modal_surf.get_rect(), border_radius=24)
        pygame.draw.rect(modal_surf, (227, 11, 93, 230), modal_surf.get_rect(), width=3, border_radius=24)

        # Header Title
        title_s = self.assets.font_title.render("Admin Control Panel", True, (255, 255, 255))
        modal_surf.blit(title_s, (40, 25))

        # Close X Button
        close_surf = self.assets.font_title.render("X", True, (255, 75, 110))
        modal_surf.blit(close_surf, (self.modal_w - 50, 20))

        # Divider line
        pygame.draw.line(modal_surf, (35, 50, 80), (40, 75), (self.modal_w - 40, 75), width=2)

        # Content Area
        content_y = 90
        sec1_s = self.assets.font_subtitle.render("Graphic Manager & Per-Image Sizing", True, (255, 45, 85))
        modal_surf.blit(sec1_s, (40, content_y))

        # Graphic Manager Grid
        grid_x = 40
        grid_y = content_y + 40
        logo_scales = self.config_data.get("logo_scales", {})

        for idx, img in enumerate(self.available_images):
            card_x = grid_x + (idx % 3) * 280
            card_y = grid_y + (idx // 3) * 220
            
            card_rect = pygame.Rect(card_x, card_y, 260, 205)
            pygame.draw.rect(modal_surf, (10, 16, 28, 220), card_rect, border_radius=12)
            pygame.draw.rect(modal_surf, (40, 55, 85), card_rect, width=1, border_radius=12)

            # Thumbnail
            thumb = self.assets.get_logo_surface(img, variant='small', scale_mult=1.0)
            if thumb:
                modal_surf.blit(thumb, (card_x + 130 - thumb.get_width()//2, card_y + 10))

            # Label
            lbl_s = self.assets.font_badge.render(img, True, (240, 245, 255))
            modal_surf.blit(lbl_s, (card_x + 130 - lbl_s.get_width()//2, card_y + 85))

            # Primary Radio
            is_pri = (self.config_data.get("primary_logo") == img)
            radio_color = (16, 185, 129) if is_pri else (100, 115, 140)
            radio_txt = self.assets.font_stats.render("[x] Primary" if is_pri else "[ ] Primary", True, radio_color)
            modal_surf.blit(radio_txt, (card_x + 20, card_y + 118))

            # Orbit Checkbox
            is_orb = (img in self.config_data.get("active_logos", []))
            check_color = (0, 245, 255) if is_orb else (100, 115, 140)
            check_txt = self.assets.font_stats.render("[x] Orbit" if is_orb else "[ ] Orbit", True, check_color)
            modal_surf.blit(check_txt, (card_x + 145, card_y + 118))

            # Size Slider Bar
            scale_val = logo_scales.get(img, 1.0)
            pct_str = f"Scale: {int(scale_val * 100)}%"
            sc_s = self.assets.font_stats.render(pct_str, True, (255, 215, 0))
            modal_surf.blit(sc_s, (card_x + 130 - sc_s.get_width()//2, card_y + 150))

            slider_bar = pygame.Rect(card_x + 15, card_y + 175, 230, 8)
            pygame.draw.rect(modal_surf, (30, 45, 70), slider_bar, border_radius=4)
            fill_w = int(230 * ((scale_val - 0.3) / (2.5 - 0.3)))
            fill_rect = pygame.Rect(card_x + 15, card_y + 175, max(4, fill_w), 8)
            pygame.draw.rect(modal_surf, (255, 45, 85), fill_rect, border_radius=4)
            
            # Knob
            knob_cx = card_x + 15 + fill_w
            pygame.draw.circle(modal_surf, (255, 255, 255), (knob_cx, card_y + 179), 8)

        # Section 2: Text Strings Configuration
        text_fields_y = grid_y + math.ceil(len(self.available_images) / 3.0) * 220 + 30
        sec2_s = self.assets.font_subtitle.render("Display Strings Configuration", True, (255, 45, 85))
        modal_surf.blit(sec2_s, (40, text_fields_y - 35))

        fields = [
            ("header_title", "Top Title"),
            ("header_subtitle", "Top Subtitle"),
            ("idle_cta_text", "Idle CTA Text"),
            ("hud_touch_label", "Touch Label"),
            ("hud_mode_idle_text", "Idle Mode Text"),
            ("hud_mode_interactive_text", "Active Mode Text"),
            ("touch_badge_label", "Finger Format")
        ]

        for i, (key, label) in enumerate(fields):
            fy = text_fields_y + i * 55
            lbl = self.assets.font_stats.render(label, True, (180, 200, 225))
            modal_surf.blit(lbl, (40, fy + 8))

            val_str = str(self.config_data.get(key, ""))
            is_active = (self.active_text_field == key)
            border_color = (255, 45, 85) if is_active else (45, 65, 95)
            
            box_rect = pygame.Rect(300, fy, 570, 42)
            pygame.draw.rect(modal_surf, (10, 16, 28, 230), box_rect, border_radius=8)
            pygame.draw.rect(modal_surf, border_color, box_rect, width=2 if is_active else 1, border_radius=8)

            txt_s = self.assets.font_badge.render(val_str + ("|" if is_active and (int(time.time()*2)%2==0) else ""), True, (255, 255, 255))
            modal_surf.blit(txt_s, (315, fy + 10))

        # Footer Action Buttons
        save_rect = pygame.Rect(40, self.modal_h - 85, 400, 60)
        cancel_rect = pygame.Rect(480, self.modal_h - 85, 400, 60)

        pygame.draw.rect(modal_surf, (16, 185, 129), save_rect, border_radius=14)
        pygame.draw.rect(modal_surf, (225, 29, 72), cancel_rect, border_radius=14)

        sv_txt = self.assets.font_title.render("SAVE & APPLY", True, (255, 255, 255))
        cn_txt = self.assets.font_title.render("CANCEL", True, (255, 255, 255))

        modal_surf.blit(sv_txt, (40 + (400 - sv_txt.get_width())//2, self.modal_h - 85 + (60 - sv_txt.get_height())//2))
        modal_surf.blit(cn_txt, (480 + (400 - cn_txt.get_width())//2, self.modal_h - 85 + (60 - cn_txt.get_height())//2))

        # Blit main modal surface to screen
        surface.blit(modal_surf, (self.modal_x, self.modal_y))

        # Render custom glowing physical mouse cursor pointer
        mx, my = pygame.mouse.get_pos()
        cursor_color = (0, 245, 255)
        pygame.draw.polygon(surface, cursor_color, [(mx, my), (mx + 18, my + 14), (mx + 12, my + 18), (mx + 8, my + 24), (mx, my)])
        pygame.draw.polygon(surface, (255, 255, 255), [(mx, my), (mx + 18, my + 14), (mx + 12, my + 18), (mx + 8, my + 24), (mx, my)], width=2)

        # Draw toast if active
        if time.time() - self.toast_time < 3.0:
            toast_surf = pygame.Surface((600, 60), pygame.SRCALPHA)
            pygame.draw.rect(toast_surf, (16, 185, 129, 240), toast_surf.get_rect(), border_radius=12)
            t_txt = self.assets.font_badge.render(self.toast_message, True, (255, 255, 255))
            toast_surf.blit(t_txt, ((600 - t_txt.get_width())//2, (60 - t_txt.get_height())//2))
            surface.blit(toast_surf, ((self.width - 600)//2, 100))
