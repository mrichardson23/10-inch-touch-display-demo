import pygame
import math
import random
import time
import colorsys

class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, lifetime=0.6, size=None):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2.0, 10.0) if vx is None else 1.0
        self.vx = math.cos(angle) * speed if vx is None else vx
        self.vy = math.sin(angle) * speed if vy is None else vy
        self.lifetime = lifetime
        self.age = 0.0
        self.size = random.uniform(4.0, 12.0) if size is None else size

    def update(self, dt):
        self.x += self.vx * dt * 60.0
        self.y += self.vy * dt * 60.0
        self.vy += 0.08 * dt * 60.0
        self.age += dt
        return self.age < self.lifetime

    def draw(self, surface):
        progress = self.age / self.lifetime
        alpha = max(0, int(255 * (1.0 - progress)))
        cur_size = max(1, int(self.size * (1.0 - progress * 0.5)))
        color_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
        
        s = pygame.Surface((cur_size * 2, cur_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, color_with_alpha, (cur_size, cur_size), cur_size)
        surface.blit(s, (int(self.x - cur_size), int(self.y - cur_size)))

class Ripple:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 10.0
        self.max_radius = random.uniform(80.0, 150.0)
        self.speed = random.uniform(160.0, 260.0)
        self.alive = True

    def update(self, dt):
        self.radius += self.speed * dt
        if self.radius >= self.max_radius:
            self.alive = False

    def draw(self, surface):
        progress = self.radius / self.max_radius
        alpha = max(0, int(255 * (1.0 - progress)))
        thick = max(1, int(3 * (1.0 - progress)))
        
        r_int = int(self.radius)
        s = pygame.Surface((r_int * 2 + 8, r_int * 2 + 8), pygame.SRCALPHA)
        color_a = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(s, color_a, (r_int + 4, r_int + 4), r_int, thick)
        surface.blit(s, (int(self.x - r_int - 4), int(self.y - r_int - 4)))

class EffectEngine:
    def __init__(self, assets, width=1200, height=1920):
        self.assets = assets
        self.width = width
        self.height = height
        self.particles = []
        self.ripples = []
        self.bg_time = 0.0
        self.idle_particles = []
        self.admin_toast_time = 0.0
        
        for _ in range(50):
            self.idle_particles.append({
                'x': random.uniform(0, width),
                'y': random.uniform(0, height),
                'speed': random.uniform(0.5, 2.0),
                'radius': random.uniform(2, 5),
                'hue': random.uniform(0, 1)
            })

    def trigger_admin_toast(self):
        self.admin_toast_time = time.time()

    def update(self, dt, is_idle, total_active_touches=0):
        self.bg_time += dt

        self.ripples = [r for r in self.ripples if r.alive]
        for r in self.ripples:
            r.update(dt)

        self.particles = [p for p in self.particles if p.update(dt)]

        if total_active_touches > 0:
            max_particles = max(35, int(160 / math.sqrt(total_active_touches)))
            if len(self.particles) > max_particles:
                self.particles = self.particles[-max_particles:]

        if is_idle:
            for p in self.idle_particles:
                p['y'] -= p['speed'] * dt * 60.0
                if p['y'] < -10:
                    p['y'] = self.height + 10
                    p['x'] = random.uniform(0, self.width)
                p['hue'] = (p['hue'] + 0.1 * dt) % 1.0

            if random.random() < 0.03:
                fx = random.uniform(100, self.width - 100)
                fy = random.uniform(300, self.height - 400)
                hue = random.random()
                r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.9, 1.0)]
                self.spawn_firework(fx, fy, (r, g, b))

    def spawn_touch_effects(self, touch, total_active_touches=1):
        spawn_chance = max(0.2, 1.0 - (total_active_touches - 1) * 0.08)
        if random.random() < spawn_chance:
            p_count = 1 if total_active_touches > 3 else 2
            for _ in range(p_count):
                self.particles.append(Particle(
                    touch.x + random.uniform(-6, 6),
                    touch.y + random.uniform(-6, 6),
                    touch.color,
                    vx=touch.dx * 0.25 + random.uniform(-2, 2),
                    vy=touch.dy * 0.25 + random.uniform(-2, 2),
                    lifetime=random.uniform(0.25, 0.55),
                    size=random.uniform(5, 12)
                ))

        ripple_chance = 0.12 / math.sqrt(max(1, total_active_touches))
        if random.random() < ripple_chance or math.hypot(touch.dx, touch.dy) > (15 + total_active_touches * 2):
            self.ripples.append(Ripple(touch.x, touch.y, touch.color))

    def spawn_firework(self, x, y, color):
        self.ripples.append(Ripple(x, y, color))
        for _ in range(18):
            self.particles.append(Particle(
                x, y, color,
                lifetime=random.uniform(0.6, 1.2),
                size=random.uniform(5, 14)
            ))

    def draw_background(self, surface):
        surface.fill((10, 14, 26))

        t = self.bg_time
        for i in range(4):
            wave_y = self.height * (0.25 + 0.2 * i) + math.sin(t * 0.8 + i) * 60
            hue = (t * 0.05 + i * 0.2) % 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.8, 0.6)]
            
            wave_surf = pygame.Surface((self.width, 240), pygame.SRCALPHA)
            points = [(0, 240)]
            for x in range(0, self.width + 20, 20):
                y = 120 + math.sin(x * 0.005 + t * 1.5 + i) * 50 + math.cos(x * 0.01 - t) * 30
                points.append((x, int(y)))
            points.append((self.width, 240))
            
            pygame.draw.polygon(wave_surf, (r, g, b, 25), points)
            surface.blit(wave_surf, (0, int(wave_y - 120)))

    def draw_idle_mode(self, surface, config):
        """Draw dazzling idle showcase with orbiting active logo images (without connecting line)."""
        t = self.bg_time

        # Ambient background stars
        for p in self.idle_particles:
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(p['hue'], 0.8, 1.0)]
            s = pygame.Surface((p['radius']*2+4, p['radius']*2+4), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, 180), (p['radius']+2, p['radius']+2), p['radius'])
            surface.blit(s, (int(p['x']), int(p['y'])))

        cx = self.width / 2
        cy = self.height * 0.42

        primary_logo = config.get("primary_logo", "MFH.png")
        active_logos = config.get("active_logos", ["MFH.png", "logo.png"])
        if not isinstance(active_logos, list) or len(active_logos) == 0:
            active_logos = [primary_logo]

        if primary_logo not in active_logos:
            active_logos.insert(0, primary_logo)
        else:
            active_logos.remove(primary_logo)
            active_logos.insert(0, primary_logo)

        N = len(active_logos)

        if N >= 2:
            # Multi-logo orbiting double-helix animation
            radius_x = 180.0
            radius_y = 90.0
            
            positions = []
            for idx, logo_name in enumerate(active_logos):
                angle = t * 1.4 + (idx * 2 * math.pi / N)
                lx = cx + radius_x * math.cos(angle)
                ly = cy + radius_y * math.sin(angle) + math.sin(t * 2.0 + idx) * 15.0
                is_primary = (logo_name == primary_logo)
                positions.append((lx, ly, logo_name, idx, is_primary))

            # Draw each orbiting logo freely (connecting line removed as requested)
            for lx, ly, logo_name, idx, is_primary in positions:
                hue = (t * 0.15 + idx / N) % 1.0
                sr, sg, sb = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.9, 1.0)]
                
                glow_radius = 130 if is_primary else 85
                variant = 'large' if is_primary else 'medium'

                glow = self.assets.get_glow_circle(glow_radius, (sr, sg, sb))
                surface.blit(glow, (int(lx - glow_radius), int(ly - glow_radius)))

                logo_surf = self.assets.get_logo_surface(logo_name, variant=variant)
                rect = logo_surf.get_rect(center=(int(lx), int(ly)))
                surface.blit(logo_surf, rect)

        else:
            logo_name = primary_logo
            fy = cy + math.sin(t * 1.8) * 20.0

            for i in range(3):
                orbit_angle = t * (1.2 + i * 0.4) + i * (math.pi * 2 / 3)
                sat_x = cx + 180 * math.cos(orbit_angle)
                sat_y = fy + 60 * math.sin(orbit_angle)
                sat_hue = (t * 0.2 + i * 0.33) % 1.0
                sr, sg, sb = [int(c * 255) for c in colorsys.hsv_to_rgb(sat_hue, 0.9, 1.0)]
                glow = self.assets.get_glow_circle(45, (sr, sg, sb))
                surface.blit(glow, (int(sat_x - 45), int(sat_y - 45)))

            logo_glow = self.assets.get_glow_circle(140, (227, 11, 93))
            surface.blit(logo_glow, (int(cx - 140), int(fy - 140)))

            logo_surf = self.assets.get_logo_surface(logo_name, variant='large')
            rect = logo_surf.get_rect(center=(int(cx), int(fy)))
            surface.blit(logo_surf, rect)

        cta_text = config.get("idle_cta_text", "TOUCH THE SCREEN WITH UP TO 10 FINGERS")
        pulse = int(200 + 55 * math.sin(t * 4))
        cta_surf = self.assets.font_badge.render(cta_text, True, (255, 255, 255))
        cta_rect = cta_surf.get_rect(center=(self.width // 2, int(self.height * 0.68)))
        
        bg_card = pygame.Surface((cta_rect.width + 40, cta_rect.height + 24), pygame.SRCALPHA)
        pygame.draw.rect(bg_card, (20, 30, 50, 200), bg_card.get_rect(), border_radius=16)
        pygame.draw.rect(bg_card, (227, 11, 93, pulse), bg_card.get_rect(), width=2, border_radius=16)
        
        surface.blit(bg_card, (cta_rect.x - 20, cta_rect.y - 12))
        surface.blit(cta_surf, cta_rect)

    def draw_interactive_mode(self, surface, touches, config):
        """Draw interactive multi-touch visualization."""
        n = len(touches)
        if n >= 2:
            for i in range(n):
                for j in range(i + 1, n):
                    t1, t2 = touches[i], touches[j]
                    dist = math.hypot(t1.x - t2.x, t1.y - t2.y)
                    alpha = max(30, int(220 * (1.0 - min(1.0, dist / 900.0))))
                    
                    line_color = (
                        (t1.color[0] + t2.color[0]) // 2,
                        (t1.color[1] + t2.color[1]) // 2,
                        (t1.color[2] + t2.color[2]) // 2,
                        alpha
                    )
                    
                    line_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    pygame.draw.line(line_surf, line_color, (int(t1.x), int(t1.y)), (int(t2.x), int(t2.y)), width=3)
                    surface.blit(line_surf, (0, 0))

        for r in self.ripples:
            r.draw(surface)

        for p in self.particles:
            p.draw(surface)

        badge_template = config.get("touch_badge_label", "FINGER #{slot} ({x}, {y})")

        for t in touches:
            glow = self.assets.get_glow_circle(50 if n > 4 else 60, t.color)
            surface.blit(glow, (int(t.x - glow.get_width()//2), int(t.y - glow.get_height()//2)))

            pygame.draw.circle(surface, (255, 255, 255), (int(t.x), int(t.y)), 30, width=2)
            pygame.draw.circle(surface, t.color, (int(t.x), int(t.y)), 16)
            pygame.draw.circle(surface, (255, 255, 255), (int(t.x), int(t.y)), 5)

            try:
                badge_str = badge_template.format(slot=t.slot + 1, x=int(t.x), y=int(t.y))
            except Exception:
                badge_str = f"FINGER #{t.slot + 1} ({int(t.x)}, {int(t.y)})"

            txt_s = self.assets.font_badge.render(badge_str, True, (255, 255, 255))
            
            bx = max(10, min(self.width - txt_s.get_width() - 30, int(t.x) - txt_s.get_width() // 2))
            by = int(t.y) - 65 if t.y > 120 else int(t.y) + 45
            
            card = pygame.Surface((txt_s.get_width() + 20, txt_s.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(card, (15, 20, 35, 210), card.get_rect(), border_radius=8)
            pygame.draw.rect(card, t.color, card.get_rect(), width=2, border_radius=8)
            card.blit(txt_s, (10, 5))
            
            surface.blit(card, (bx, by))

    def draw_header_overlay(self, surface, config, active_touch_count, fps, is_idle):
        """Draw top banner header card and bottom touch HUD status bar."""
        title_text = config.get("header_title", "Raspberry Pi's new 10-inch Touch Display 2")
        subtitle_text = config.get("header_subtitle", "1200×1920 • 10-Point Multi-Touch Capacitive Display")
        hud_touch_label = config.get("hud_touch_label", "TOUCH POINTS")
        hud_idle_text = config.get("hud_mode_idle_text", "MODE: DEMO IDLE")
        hud_interactive_text = config.get("hud_mode_interactive_text", "MODE: MULTI-TOUCH INTERACTIVE")

        card_h = 160
        header_card = pygame.Surface((self.width - 40, card_h), pygame.SRCALPHA)
        pygame.draw.rect(header_card, (15, 22, 40, 210), header_card.get_rect(), border_radius=20)
        pygame.draw.rect(header_card, (227, 11, 93, 180), header_card.get_rect(), width=2, border_radius=20)

        primary_logo = config.get("primary_logo", "MFH.png")
        small_logo = self.assets.get_logo_surface(primary_logo, variant='small')
        if small_logo:
            header_card.blit(small_logo, (20, (card_h - small_logo.get_height()) // 2))

        t_surf = self.assets.font_title.render(title_text, True, (255, 255, 255))
        sub_surf = self.assets.font_subtitle.render(subtitle_text, True, (180, 200, 225))

        header_card.blit(t_surf, (125, 35))
        header_card.blit(sub_surf, (127, 95))

        surface.blit(header_card, (20, 20))

        hud_h = 80
        hud_card = pygame.Surface((self.width - 40, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_card, (15, 22, 40, 210), hud_card.get_rect(), border_radius=16)
        
        cnt_color = (57, 255, 20) if active_touch_count > 0 else (140, 160, 180)
        cnt_str = f"{hud_touch_label}: {active_touch_count} / 10"
        cnt_surf = self.assets.font_stats.render(cnt_str, True, cnt_color)
        hud_card.blit(cnt_surf, (30, 26))

        mode_str = hud_idle_text if is_idle else hud_interactive_text
        mode_color = (255, 215, 0) if is_idle else (0, 245, 255)
        mode_surf = self.assets.font_stats.render(mode_str, True, mode_color)
        hud_card.blit(mode_surf, (self.width - mode_surf.get_width() - 170, 26))

        fps_surf = self.assets.font_stats.render(f"{int(fps)} FPS", True, (150, 170, 190))
        hud_card.blit(fps_surf, (self.width - fps_surf.get_width() - 70, 26))

        surface.blit(hud_card, (20, self.height - hud_h - 20))

        if time.time() - self.admin_toast_time < 4.0:
            toast_w, toast_h = 760, 70
            toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
            pygame.draw.rect(toast_surf, (16, 185, 129, 235), toast_surf.get_rect(), border_radius=16)
            
            txt1 = self.assets.font_badge.render("🍓 LAUNCHING ADMIN PANEL AT: http://192.168.86.156:8080", True, (255, 255, 255))
            toast_surf.blit(txt1, ((toast_w - txt1.get_width()) // 2, (toast_h - txt1.get_height()) // 2))
            
            surface.blit(toast_surf, ((self.width - toast_w) // 2, self.height // 2 - 35))
