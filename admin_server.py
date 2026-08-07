import os
import json
import threading
from flask import Flask, request, jsonify, render_template_string

def get_config_paths():
    user_config_dir = os.path.expanduser("~/.config/rpi-touch-demo")
    user_config_path = os.path.join(user_config_dir, "config.json")
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_cfg_path = os.path.join(app_dir, "config.json")
    return user_config_path, app_cfg_path

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

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raspberry Pi Touch Display Demo - Admin Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #141c2e;
            --card-border: #23314d;
            --accent-red: #e30b5d;
            --accent-pink: #ff2d55;
            --accent-green: #10b981;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 30px 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            max-width: 900px;
            width: 100%;
        }

        .header {
            text-align: center;
            margin-bottom: 25px;
        }

        .header h1 {
            font-size: 2.2rem;
            font-weight: 800;
            margin: 0 0 10px 0;
            background: linear-gradient(135deg, #ff2d55, #e30b5d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p {
            color: var(--text-muted);
            font-size: 1.1rem;
            margin: 0;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }

        .card-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 20px;
            color: #ffffff;
            border-bottom: 2px solid var(--accent-red);
            padding-bottom: 8px;
            display: inline-block;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }

        .image-card {
            background: rgba(10, 15, 26, 0.6);
            border: 2px solid var(--card-border);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .image-card:hover {
            border-color: var(--accent-pink);
        }

        .image-card img {
            max-width: 100px;
            max-height: 100px;
            object-fit: contain;
            margin-bottom: 12px;
        }

        .image-card label {
            display: block;
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 8px;
            word-break: break-all;
        }

        .options-row {
            display: flex;
            justify-content: space-around;
            margin-top: 10px;
            font-size: 0.85rem;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 8px;
        }

        .scale-box {
            margin-top: 12px;
            background: rgba(255, 255, 255, 0.03);
            padding: 10px;
            border-radius: 8px;
            text-align: left;
        }

        .scale-box label {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .scale-slider-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .scale-slider-row input[type="range"] {
            flex: 1;
            accent-color: var(--accent-pink);
        }

        .scale-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--accent-pink);
            min-width: 45px;
        }

        .form-group {
            margin-bottom: 18px;
        }

        .form-group label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .form-group input[type="text"],
        .form-group input[type="number"] {
            width: 100%;
            padding: 12px 14px;
            background: rgba(10, 15, 26, 0.8);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: #ffffff;
            font-family: inherit;
            font-size: 0.95rem;
            box-sizing: border-box;
        }

        .btn-submit {
            width: 100%;
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-red));
            color: #ffffff;
            font-weight: 700;
            font-size: 1.15rem;
            border: none;
            padding: 18px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px rgba(227, 11, 93, 0.4);
        }

        .btn-submit:hover {
            opacity: 0.95;
            transform: translateY(-2px);
        }

        .toast {
            display: none;
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            font-weight: 800;
            font-size: 1.1rem;
            text-align: center;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
            border: 2px solid #34d399;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Raspberry Pi Touch Display 2</h1>
            <p>Admin Control Panel — Live Customization</p>
        </div>

        <div id="toast" class="toast">SETTINGS SAVED PERSISTENTLY & RELOADED LIVE ON DISPLAY</div>

        <form id="adminForm" action="/save" method="POST">

            <!-- GRAPHIC MANAGER & PER-GRAPHIC SIZING -->
            <div class="card">
                <h2 class="card-title">Graphic Manager & Size Scales</h2>
                <p style="font-size: 0.9rem; color: var(--text-muted); margin-top: -10px; margin-bottom: 15px;">
                    Select graphics to show, choose the Primary Graphic (layered on top), and adjust individual size scaling.
                </p>
                <div class="grid">
                    {% for img in available_images %}
                    <div class="image-card">
                        <img src="/image/{{ img }}" alt="{{ img }}">
                        <label>{{ img }}</label>
                        <div class="options-row">
                            <div>
                                <input type="radio" id="primary_{{ img }}" name="primary_logo" value="{{ img }}" {% if config.get('primary_logo') == img %}checked{% endif %}>
                                <label for="primary_{{ img }}" style="display:inline; cursor:pointer;">Primary</label>
                            </div>
                            <div>
                                <input type="checkbox" id="active_{{ img }}" name="active_logos" value="{{ img }}" {% if img in config.get('active_logos', []) %}checked{% endif %}>
                                <label for="active_{{ img }}" style="display:inline; cursor:pointer;">Orbit</label>
                            </div>
                        </div>
                        <div class="scale-box">
                            <label>Size Scale</label>
                            <div class="scale-slider-row">
                                <input type="range" name="scale_{{ img }}" min="0.3" max="2.5" step="0.05" value="{{ config.get('logo_scales', {}).get(img, 1.0) }}" oninput="document.getElementById('val_{{ loop.index }}').innerText = Math.round(this.value * 100) + '%';">
                                <span class="scale-val" id="val_{{ loop.index }}">{{ (config.get('logo_scales', {}).get(img, 1.0) * 100)|int }}%</span>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- DISPLAY TEXT CONFIGURATION -->
            <div class="card">
                <h2 class="card-title">Display Strings Configuration</h2>
                
                <div class="form-group">
                    <label>Top Header Title</label>
                    <input type="text" name="header_title" value="{{ config.get('header_title', '') }}">
                </div>

                <div class="form-group">
                    <label>Top Header Subtitle</label>
                    <input type="text" name="header_subtitle" value="{{ config.get('header_subtitle', '') }}">
                </div>

                <div class="form-group">
                    <label>Idle Mode CTA Button Text</label>
                    <input type="text" name="idle_cta_text" value="{{ config.get('idle_cta_text', '') }}">
                </div>

                <div class="form-group">
                    <label>HUD Touch Points Label</label>
                    <input type="text" name="hud_touch_label" value="{{ config.get('hud_touch_label', '') }}">
                </div>

                <div class="form-group">
                    <label>HUD Idle Mode Text</label>
                    <input type="text" name="hud_mode_idle_text" value="{{ config.get('hud_mode_idle_text', '') }}">
                </div>

                <div class="form-group">
                    <label>HUD Interactive Mode Text</label>
                    <input type="text" name="hud_mode_interactive_text" value="{{ config.get('hud_mode_interactive_text', '') }}">
                </div>

                <div class="form-group">
                    <label>Finger Badge Label Format (Template: {slot}, {x}, {y})</label>
                    <input type="text" name="touch_badge_label" value="{{ config.get('touch_badge_label', '') }}">
                </div>

                <div class="form-group">
                    <label>Idle Timeout (Seconds before returning to Standby Mode)</label>
                    <input type="number" step="0.5" name="idle_timeout_seconds" value="{{ config.get('idle_timeout_seconds', 4.0) }}">
                </div>
            </div>

            <button type="submit" id="saveBtn" class="btn-submit">Save & Reload Settings</button>
        </form>
    </div>

    <script>
        const form = document.getElementById('adminForm');
        const saveBtn = document.getElementById('saveBtn');
        const toast = document.getElementById('toast');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            saveBtn.disabled = true;
            saveBtn.innerHTML = "Saving Changes...";
            saveBtn.style.opacity = "0.7";

            try {
                const formData = new FormData(form);
                const resp = await fetch('/save', {
                    method: 'POST',
                    body: formData
                });
                
                if (resp.ok) {
                    saveBtn.innerHTML = "Saved Successfully!";
                    saveBtn.style.background = "linear-gradient(135deg, #10b981, #059669)";
                    toast.style.display = 'block';
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    
                    setTimeout(() => {
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = "Save & Reload Settings";
                        saveBtn.style.background = "linear-gradient(135deg, var(--accent-pink), var(--accent-red))";
                        saveBtn.style.opacity = "1";
                    }, 2500);

                    setTimeout(() => { 
                        toast.style.display = 'none'; 
                    }, 5000);
                } else {
                    const text = await resp.text();
                    alert("Error saving settings: " + text);
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = "Save & Reload Settings";
                    saveBtn.style.opacity = "1";
                }
            } catch (err) {
                alert("Connection error: " + err);
                saveBtn.disabled = false;
                saveBtn.innerHTML = "Save & Reload Settings";
                saveBtn.style.opacity = "1";
            }
        });
    </script>
</body>
</html>
"""

class AdminServer:
    def __init__(self, port=8080):
        self.port = port
        self.app = Flask(__name__)
        self.user_cfg_path, self.app_cfg_path = get_config_paths()
        self.setup_routes()

    def load_current_config(self):
        cfg = {
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
            "admin_port": self.port
        }
        if os.path.exists(self.app_cfg_path):
            try:
                with open(self.app_cfg_path, "r") as f:
                    cfg.update(json.load(f))
            except Exception:
                pass
        if os.path.exists(self.user_cfg_path):
            try:
                with open(self.user_cfg_path, "r") as f:
                    cfg.update(json.load(f))
            except Exception:
                pass
        return cfg

    def setup_routes(self):
        @self.app.route("/")
        def index():
            config = self.load_current_config()
            images = get_available_images()
            return render_template_string(INDEX_HTML, config=config, available_images=images)

        @self.app.route("/image/<filename>")
        def get_image(filename):
            from flask import send_from_directory
            app_dir = os.path.dirname(os.path.abspath(__file__))
            return send_from_directory(app_dir, filename)

        @self.app.route("/save", methods=["POST"])
        def save():
            config = self.load_current_config()
            
            # String fields
            for key in ["header_title", "header_subtitle", "idle_cta_text", 
                        "hud_touch_label", "hud_mode_idle_text", 
                        "hud_mode_interactive_text", "touch_badge_label"]:
                if key in request.form:
                    config[key] = request.form[key]

            # Primary logo
            if "primary_logo" in request.form:
                config["primary_logo"] = request.form["primary_logo"]

            # Active logos
            config["active_logos"] = request.form.getlist("active_logos")

            # Per-graphic scale multipliers
            logo_scales = config.get("logo_scales", {})
            available_imgs = get_available_images()
            for img in available_imgs:
                scale_key = f"scale_{img}"
                if scale_key in request.form:
                    try:
                        logo_scales[img] = round(float(request.form[scale_key]), 2)
                    except Exception:
                        logo_scales[img] = 1.0
            config["logo_scales"] = logo_scales

            # Idle timeout
            if "idle_timeout_seconds" in request.form:
                try:
                    config["idle_timeout_seconds"] = float(request.form["idle_timeout_seconds"])
                except Exception:
                    pass

            # Save persistently to user config
            try:
                os.makedirs(os.path.dirname(self.user_cfg_path), exist_ok=True)
                with open(self.user_cfg_path, "w") as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                print(f"[AdminServer] Error writing user config: {e}")

            # Save to app config
            try:
                with open(self.app_cfg_path, "w") as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                print(f"[AdminServer] Error writing app config: {e}")

            return jsonify({"status": "ok", "config": config})

    def start(self):
        t = threading.Thread(target=lambda: self.app.run(host="0.0.0.0", port=self.port, debug=False, use_reloader=False), daemon=True)
        t.start()
        print(f"[AdminServer] Admin web panel listening at http://0.0.0.0:{self.port}")
