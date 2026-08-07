import pygame
import os
import math
from PIL import Image, ImageDraw

class AssetManager:
    def __init__(self, width=1200, height=1920):
        self.width = width
        self.height = height
        self.raw_images = {} # filename -> Surface (original convert_alpha)
        self.scaled_cache = {} # (filename, variant, scale_mult) -> Surface
        self.glow_circle_surfs = {}
        self.fonts = {}

    def init(self):
        """Initialize fonts and pre-generate high quality graphics."""
        pygame.font.init()
        try:
            self.font_title = pygame.font.SysFont("DejaVu Sans", 42, bold=True)
            self.font_subtitle = pygame.font.SysFont("DejaVu Sans", 24)
            self.font_badge = pygame.font.SysFont("DejaVu Sans", 20, bold=True)
            self.font_large = pygame.font.SysFont("DejaVu Sans", 72, bold=True)
            self.font_stats = pygame.font.SysFont("Monospace", 22, bold=True)
        except Exception:
            self.font_title = pygame.font.Font(None, 48)
            self.font_subtitle = pygame.font.Font(None, 28)
            self.font_badge = pygame.font.Font(None, 24)
            self.font_large = pygame.font.Font(None, 80)
            self.font_stats = pygame.font.Font(None, 26)

        self.preload_all_available_images()
        self.precache_glow_circles()

    def get_available_image_files(self):
        """Scan directory for available PNG image assets."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        png_files = []
        try:
            for f in sorted(os.listdir(base_dir)):
                if f.lower().endswith(".png") and not f.startswith("."):
                    png_files.append(f)
        except Exception as e:
            print(f"[AssetManager] Error listing images: {e}")
        return png_files

    def preload_all_available_images(self):
        """Preload all PNG files in directory."""
        available = self.get_available_image_files()
        for filename in available:
            self.load_raw_image_asset(filename)
        
        if "default_rpi" not in self.raw_images:
            self.raw_images["default_rpi"] = self.create_raspberry_logo(size=240)

    def load_raw_image_asset(self, filename):
        """Load single raw image file."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_dir, filename)
        if os.path.exists(img_path):
            try:
                img = pygame.image.load(img_path).convert_alpha()
                self.raw_images[filename] = img
                print(f"[AssetManager] Loaded raw image asset '{filename}' ({img.get_width()}x{img.get_height()})")
                return img
            except Exception as e:
                print(f"[AssetManager] Error loading image {filename}: {e}")
        return None

    def get_logo_surface(self, filename, variant='large', scale_mult=1.0):
        """Return cached logo surface with custom scale multiplier."""
        # Ensure scale_mult is float and rounded for caching
        try:
            scale_mult = round(float(scale_mult), 2)
        except Exception:
            scale_mult = 1.0

        scale_mult = max(0.2, min(3.0, scale_mult))
        cache_key = (filename, variant, scale_mult)
        
        if cache_key in self.scaled_cache:
            return self.scaled_cache[cache_key]

        # Check if raw image is loaded
        if filename not in self.raw_images:
            img = self.load_raw_image_asset(filename)
            if not img:
                filename = "default_rpi"

        img = self.raw_images.get(filename) or self.raw_images.get("default_rpi")
        w, h = img.get_size()
        
        base_target = 240.0 if variant == 'large' else (150.0 if variant == 'medium' else 85.0)
        target_max = base_target * scale_mult

        scale = target_max / max(w, h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))

        scaled_surf = pygame.transform.smoothscale(img, (new_w, new_h))
        self.scaled_cache[cache_key] = scaled_surf
        return scaled_surf

    def create_raspberry_logo(self, size=200):
        """Programmatically generate fallback vector Raspberry Pi logo."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        s = size / 200.0
        cx, cy = size / 2, size * 0.55

        berry_red = (227, 11, 93, 255)
        leaf_green = (117, 186, 25, 255)
        highlight_red = (255, 75, 135, 255)

        drupelets = [
            (cx - 32*s, cy - 35*s, 22*s),
            (cx,         cy - 42*s, 24*s),
            (cx + 32*s, cy - 35*s, 22*s),
            (cx - 50*s, cy - 10*s, 24*s),
            (cx - 18*s, cy - 12*s, 25*s),
            (cx + 18*s, cy - 12*s, 25*s),
            (cx + 50*s, cy - 10*s, 24*s),
            (cx - 35*s, cy + 18*s, 24*s),
            (cx,         cy + 16*s, 26*s),
            (cx + 35*s, cy + 18*s, 24*s),
            (cx,         cy + 46*s, 23*s),
        ]

        for x, y, r in drupelets:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=berry_red)
            hr = r * 0.4
            draw.ellipse([x - r*0.5, y - r*0.5, x - r*0.5 + hr, y - r*0.5 + hr], fill=highlight_red)

        draw.polygon([
            (cx - 5*s, cy - 45*s),
            (cx - 45*s, cy - 70*s),
            (cx - 65*s, cy - 50*s),
            (cx - 30*s, cy - 38*s)
        ], fill=leaf_green)

        draw.polygon([
            (cx + 5*s, cy - 45*s),
            (cx + 45*s, cy - 70*s),
            (cx + 65*s, cy - 50*s),
            (cx + 30*s, cy - 38*s)
        ], fill=leaf_green)

        draw.polygon([
            (cx, cy - 48*s),
            (cx - 15*s, cy - 78*s),
            (cx + 15*s, cy - 78*s)
        ], fill=leaf_green)

        mode = img.mode
        data = img.tobytes()
        return pygame.image.fromstring(data, img.size, mode).convert_alpha()

    def precache_glow_circles(self):
        """Pre-render radial glowing circle surfaces."""
        for radius in [20, 40, 60, 90, 130, 180]:
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -2):
                alpha = int(255 * (1.0 - (r / radius) ** 1.5) * 0.4)
                pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), r)
            self.glow_circle_surfs[radius] = surf

    def get_glow_circle(self, radius, color):
        """Return a colored glowing circle surface."""
        keys = sorted(self.glow_circle_surfs.keys())
        cached_r = min(keys, key=lambda k: abs(k - radius))
        base_surf = self.glow_circle_surfs[cached_r].copy()
        
        color_surf = pygame.Surface(base_surf.get_size(), pygame.SRCALPHA)
        color_surf.fill((color[0], color[1], color[2], 255))
        base_surf.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        if cached_r != radius:
            return pygame.transform.smoothscale(base_surf, (radius * 2, radius * 2))
        return base_surf
