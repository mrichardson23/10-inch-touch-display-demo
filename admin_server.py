import os
import json
import threading
from flask import Flask, request, jsonify, render_template_string

def get_config_paths():
    user_cfg_dir = os.path.expanduser("~/.config/rpi-touch-demo")
    os.makedirs(user_cfg_dir, exist_ok=True)
    user_cfg_path = os.path.join(user_cfg_dir, "config.json")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_cfg_path = os.path.join(base_dir, "config.json")
    return user_cfg_path, app_cfg_path

def get_available_images():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    imgs = []
    try:
        for f in sorted(os.listdir(base_dir)):
            if f.lower().endswith(".png") and not f.startswith("."):
                imgs.append(f)
    except Exception:
        pass
    return imgs

class AdminServer:
    def __init__(self, config_path=None, port=8080):
        self.user_cfg_path, self.app_cfg_path = get_config_paths()
        self.port = port
        self.app = Flask(__name__)
        self.server_thread = None
        self.setup_routes()

    def load_config(self):
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
        if os.path.exists(self.app_cfg_path):
            try:
                with open(self.app_cfg_path, 'r') as f:
                    default_config.update(json.load(f))
            except Exception:
                pass

        if os.path.exists(self.user_cfg_path):
            try:
                with open(self.user_cfg_path, 'r') as f:
                    default_config.update(json.load(f))
            except Exception:
                pass

        return default_config

    def save_config(self, cfg):
        try:
            with open(self.user_cfg_path, 'w') as f:
                json.dump(cfg, f, indent=2)

            try:
                with open(self.app_cfg_path, 'w') as f:
                    json.dump(cfg, f, indent=2)
            except Exception:
                pass

            print(f"[AdminServer] Saved persistent configuration to {self.user_cfg_path}")
            return True
        except Exception as e:
            print(f"[AdminServer] Error saving config: {e}")
            return False

    def setup_routes(self):
        @self.app.route('/', methods=['GET'])
        def index():
            cfg = self.load_config()
            available_images = get_available_images()
            primary_logo = cfg.get("primary_logo", "MFH.png")
            active_logos = cfg.get("active_logos", ["MFH.png", "logo.png"])

            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Raspberry Pi Touch Display 2 - Admin Panel</title>
                <style>
                    :root {
                        --bg-color: #0b0f19;
                        --card-bg: #161f33;
                        --accent-color: #e30b5d;
                        --accent-hover: #ff2d55;
                        --text-color: #f0f4f8;
                        --text-muted: #94a3b8;
                        --border-color: #2a3754;
                    }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                        background: var(--bg-color);
                        color: var(--text-color);
                        margin: 0;
                        padding: 24px 12px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        box-sizing: border-box;
                    }
                    .container {
                        width: 100%;
                        max-width: 640px;
                        background: var(--card-bg);
                        border-radius: 16px;
                        border: 1px solid var(--border-color);
                        box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                        padding: 32px;
                        box-sizing: border-box;
                    }
                    .header {
                        display: flex;
                        align-items: center;
                        gap: 16px;
                        margin-bottom: 24px;
                        border-bottom: 1px solid var(--border-color);
                        padding-bottom: 16px;
                    }
                    .logo-icon {
                        width: 48px;
                        height: 48px;
                        background: var(--accent-color);
                        border-radius: 12px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-size: 24px;
                    }
                    h1 {
                        font-size: 22px;
                        margin: 0;
                        font-weight: 700;
                    }
                    p.subtitle {
                        color: var(--text-muted);
                        font-size: 13px;
                        margin: 4px 0 0 0;
                    }
                    .section-title {
                        font-size: 14px;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        color: var(--accent-color);
                        margin: 24px 0 12px 0;
                        border-bottom: 1px solid rgba(227, 11, 93, 0.3);
                        padding-bottom: 4px;
                    }
                    .form-group {
                        margin-bottom: 16px;
                    }
                    label {
                        display: block;
                        font-size: 13px;
                        font-weight: 600;
                        margin-bottom: 6px;
                        color: var(--text-color);
                    }
                    .hint {
                        font-size: 11px;
                        color: var(--text-muted);
                        margin-top: 4px;
                    }
                    input[type="text"], input[type="number"] {
                        width: 100%;
                        background: #0f172a;
                        border: 1px solid var(--border-color);
                        color: #fff;
                        border-radius: 8px;
                        padding: 10px 12px;
                        font-size: 14px;
                        box-sizing: border-box;
                        transition: border-color 0.2s;
                    }
                    input:focus {
                        outline: none;
                        border-color: var(--accent-color);
                    }
                    .image-select-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
                        gap: 12px;
                        margin-top: 8px;
                    }
                    .image-card {
                        background: #0f172a;
                        border: 2px solid var(--border-color);
                        border-radius: 10px;
                        padding: 12px;
                        text-align: center;
                        cursor: pointer;
                        transition: all 0.2s;
                    }
                    .image-card.selected {
                        border-color: var(--accent-color);
                        background: rgba(227, 11, 93, 0.15);
                    }
                    .image-card.primary-active {
                        border-color: #38bdf8;
                        background: rgba(56, 189, 248, 0.15);
                    }
                    .image-card input {
                        margin-right: 6px;
                    }
                    .btn-save {
                        width: 100%;
                        background: var(--accent-color);
                        color: #fff;
                        border: none;
                        border-radius: 10px;
                        padding: 14px;
                        font-size: 16px;
                        font-weight: 700;
                        cursor: pointer;
                        margin-top: 20px;
                        transition: background 0.2s;
                    }
                    .btn-save:hover {
                        background: var(--accent-hover);
                    }
                    .toast {
                        display: none;
                        background: #10b981;
                        color: white;
                        padding: 12px;
                        border-radius: 8px;
                        text-align: center;
                        margin-top: 16px;
                        font-size: 14px;
                        font-weight: 600;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo-icon">🍓</div>
                        <div>
                            <h1>Touch Display Demo Admin</h1>
                            <p class="subtitle">Raspberry Pi 10-Inch Touch Display 2 Control Panel</p>
                        </div>
                    </div>
                    <form id="configForm">
                        <div class="section-title">1. Primary Graphic Selection</div>
                        <div class="hint" style="margin-bottom: 10px;">Select which graphic is Primary (shown in top-left header & rendered larger in orbit):</div>
                        <div class="image-select-grid">
                            {% for img in available_images %}
                            <div class="image-card {% if img == primary_logo %}primary-active{% endif %}" onclick="selectPrimaryRadio(this)">
                                <input type="radio" name="primary_logo" value="{{ img }}" {% if img == primary_logo %}checked{% endif %}>
                                <strong>{{ img }}</strong>
                            </div>
                            {% endfor %}
                        </div>

                        <div class="section-title">2. Orbiting Standby Images</div>
                        <div class="hint" style="margin-bottom: 10px;">Select images to include in the Standby Mode orbit:</div>
                        <div class="image-select-grid">
                            {% for img in available_images %}
                            <div class="image-card {% if img in active_logos %}selected{% endif %}" onclick="toggleImageCard(this)">
                                <input type="checkbox" name="active_logos" value="{{ img }}" {% if img in active_logos %}checked{% endif %}>
                                <strong>{{ img }}</strong>
                            </div>
                            {% endfor %}
                        </div>

                        <div class="section-title">3. Header Banner Text</div>
                        <div class="form-group">
                            <label for="header_title">Main Header Title</label>
                            <input type="text" id="header_title" name="header_title" value="{{ cfg.get('header_title', '') }}">
                        </div>
                        <div class="form-group">
                            <label for="header_subtitle">Header Subtitle Text</label>
                            <input type="text" id="header_subtitle" name="header_subtitle" value="{{ cfg.get('header_subtitle', '') }}">
                        </div>

                        <div class="section-title">4. Idle Showcase Text & Settings</div>
                        <div class="form-group">
                            <label for="idle_cta_text">Idle Call-To-Action Banner Text</label>
                            <input type="text" id="idle_cta_text" name="idle_cta_text" value="{{ cfg.get('idle_cta_text', '') }}">
                        </div>
                        <div class="form-group">
                            <label for="idle_timeout_seconds">Idle Mode Timeout (Seconds)</label>
                            <input type="number" id="idle_timeout_seconds" name="idle_timeout_seconds" step="0.5" value="{{ cfg.get('idle_timeout_seconds', 4.0) }}">
                        </div>

                        <div class="section-title">5. Bottom HUD Status Bar Strings</div>
                        <div class="form-group">
                            <label for="hud_touch_label">Touch Points Counter Label</label>
                            <input type="text" id="hud_touch_label" name="hud_touch_label" value="{{ cfg.get('hud_touch_label', '') }}">
                        </div>
                        <div class="form-group">
                            <label for="hud_mode_idle_text">HUD Idle Mode Status Text</label>
                            <input type="text" id="hud_mode_idle_text" name="hud_mode_idle_text" value="{{ cfg.get('hud_mode_idle_text', '') }}">
                        </div>
                        <div class="form-group">
                            <label for="hud_mode_interactive_text">HUD Interactive Mode Status Text</label>
                            <input type="text" id="hud_mode_interactive_text" name="hud_mode_interactive_text" value="{{ cfg.get('hud_mode_interactive_text', '') }}">
                        </div>

                        <div class="section-title">6. Finger Touch Badge Format</div>
                        <div class="form-group">
                            <label for="touch_badge_label">Finger Badge Label Template</label>
                            <input type="text" id="touch_badge_label" name="touch_badge_label" value="{{ cfg.get('touch_badge_label', '') }}">
                            <div class="hint">Variables: {slot} (finger #), {x} (X pos), {y} (Y pos)</div>
                        </div>

                        <button type="submit" class="btn-save">Save All Settings & Primary Graphic Live</button>
                    </form>
                    <div id="toast" class="toast">✓ Primary Graphic & Settings Saved Persistently!</div>
                </div>

                <script>
                    function selectPrimaryRadio(card) {
                        const radio = card.querySelector('input[type="radio"]');
                        radio.checked = true;
                        document.querySelectorAll('input[name="primary_logo"]').forEach(r => {
                            r.closest('.image-card').classList.remove('primary-active');
                        });
                        card.classList.add('primary-active');
                    }

                    function toggleImageCard(card) {
                        const checkbox = card.querySelector('input[type="checkbox"]');
                        checkbox.checked = !checkbox.checked;
                        if (checkbox.checked) {
                            card.classList.add('selected');
                        } else {
                            card.classList.remove('selected');
                        }
                    }

                    document.getElementById('configForm').addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const selectedPrimary = document.querySelector('input[name="primary_logo"]:checked')?.value || 'MFH.png';
                        const selectedLogos = Array.from(document.querySelectorAll('input[name="active_logos"]:checked')).map(cb => cb.value);
                        
                        const formData = {
                            primary_logo: selectedPrimary,
                            active_logos: selectedLogos,
                            header_title: document.getElementById('header_title').value,
                            header_subtitle: document.getElementById('header_subtitle').value,
                            idle_cta_text: document.getElementById('idle_cta_text').value,
                            hud_touch_label: document.getElementById('hud_touch_label').value,
                            hud_mode_idle_text: document.getElementById('hud_mode_idle_text').value,
                            hud_mode_interactive_text: document.getElementById('hud_mode_interactive_text').value,
                            touch_badge_label: document.getElementById('touch_badge_label').value,
                            idle_timeout_seconds: parseFloat(document.getElementById('idle_timeout_seconds').value)
                        };
                        const res = await fetch('/api/config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(formData)
                        });
                        if (res.ok) {
                            const toast = document.getElementById('toast');
                            toast.style.display = 'block';
                            setTimeout(() => { toast.style.display = 'none'; }, 3000);
                        }
                    });
                </script>
            </body>
            </html>
            """
            return render_template_string(html, cfg=cfg, available_images=available_images, primary_logo=primary_logo, active_logos=active_logos)

        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            return jsonify(self.load_config())

        @self.app.route('/api/images', methods=['GET'])
        def get_images():
            return jsonify(get_available_images())

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            data = request.json or {}
            cfg = self.load_config()
            cfg.update(data)
            if self.save_config(cfg):
                return jsonify({"status": "success", "config": cfg})
            return jsonify({"status": "error"}), 500

    def start(self):
        def run():
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        print(f"[AdminServer] Admin web panel listening at http://0.0.0.0:{self.port}")
