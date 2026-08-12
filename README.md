# Raspberry Pi 10-Inch Touch Display 2 — Native Multi-Touch Demo

A GPU-accelerated, native Python/Pygame demonstration application engineered specifically for the **Raspberry Pi 10-Inch Touch Display 2** running on **Raspberry Pi 5** under Raspberry Pi OS (Wayland / Labwc).

---

## 🌟 Key Features

* **Native GPU Performance**: Built with Python 3, Pygame 2.6, and SDL2 running at native **1200×1920 vertical portrait orientation at 60 FPS** (no web browser runtime required for the core demo).
* **Hardware Multi-Touch Driver**: Uses direct Linux Type-B `evdev` input tracking on `/dev/input/event*` (`ili_v3` digitizer) to independently track **up to 10 multi-touch finger slots** simultaneously with distinct neon colors, expanding ripple rings, dynamic particle trails, and interactive energy tether lines.
* **Adaptive Particle Budget**: Dynamically scales particle quantities based on active finger count to maintain 60 FPS lock under heavy multi-finger interaction.
* **3D Standby Orbit Showcase**: Displays orbiting PNG graphics with glowing auras and satellite light particles around a designated **Primary Graphic**.
* **Per-Graphic Custom Size Scaling**: Admin control to scale each PNG graphic independently from **30% to 250%**. Top header caption box logo remains locked at standard size.
* **Top Layer Z-Indexing**: Primary Graphic always renders on the top layer, overlapping in front of all other orbiting graphics.
* **Dual Admin Control Panel**:
  * **In-App Native Admin Modal**: Press `TAB`, `F1`, `A`, or `C` to open a glassmorphic settings modal directly on screen. Supports physical keyboard and mouse input.
  * **Web Control Panel**: Lightweight Flask web server running on port `8080` (`http://<pi-ip>:8080`) for remote customization from any smartphone, tablet, or PC on the local network.
* **Persistent Configuration**: All text string edits, Primary Graphic selections, active orbiting images, size scale multipliers, and idle timeouts persist across system restarts in `~/.config/rpi-touch-demo/config.json`.
* **Systemd Autostart**: Runs seamlessly as a background systemd user service (`rpi-touch-demo.service`) starting on boot.
* **Taskbar Minimization**: Pressing `ESC` minimizes the demo to the taskbar without stopping the process or triggering systemd restarts.

---

## 🛠️ Prerequisites

* **Hardware**:
  * Raspberry Pi 5 (or Raspberry Pi 4)
  * Raspberry Pi 10-Inch Touch Display 2 (1200×1920 portrait resolution)
  * Multi-touch capacitive display connected via DSI/I2C
* **Operating System**:
  * Raspberry Pi OS 64-bit (Debian 12 Bookworm / Debian 13 Trixie)
  * Desktop Environment: Wayland (`labwc`)

---

## 📦 Automated Installation

1. **Clone or Copy the Repository** to your Raspberry Pi home directory:
   ```bash
   cd ~
   git clone https://github.com/<your-username>/10-inch-touch-display-demo.git rpi-touch-demo
   cd ~/rpi-touch-demo
   ```

2. **Make the Setup Script Executable**:
   ```bash
   chmod +x setup.sh
   ```

3. **Run the Setup Script**:
   ```bash
   ./setup.sh
   ```

The script automatically:
* Installs required packages (`python3-pygame`, `python3-flask`, `python3-evdev`, `python3-pil`, `chromium-browser`).
* Adds your user to the `input` Linux group for hardware multi-touch and raw keyboard access.
* Creates user configuration at `~/.config/rpi-touch-demo/config.json`.
* Configures and enables the systemd user service (`rpi-touch-demo.service`) to launch on boot.

4. **Start the Service Right Now**:
   ```bash
   systemctl --user start rpi-touch-demo.service
   ```

---

## 🎮 Controls & Shortcuts

| Action | Control |
| :--- | :--- |
| **Open In-App Admin Modal** | Press **`TAB`**, **`F1`**, **`A`**, or **`C`** on keyboard |
| **Minimize Demo to Taskbar** | Press **`ESC`** or **`Q`** on keyboard |
| **Open Web Admin Panel** | Navigate to `http://<pi-ip>:8080` in any web browser |
| **Restore Demo** | Click the demo window icon on the desktop taskbar |

---

## 🖼️ Adding Custom PNG Graphics

1. Simply copy any `.png` image into the project folder (`/home/pi/rpi-touch-demo/`):
   ```bash
   cp /path/to/my_graphic.png ~/rpi-touch-demo/
   ```
2. The application automatically detects all `.png` files in the directory.
3. Open the Admin Panel (In-App or Web) to:
   * Select `my_graphic.png` as the **Primary Graphic**.
   * Toggle `my_graphic.png` into the **Orbiting Standby** animation.
   * Adjust individual **Size Scale sliders** (30% – 250%).

---

## ⚙️ Configuration File

Configuration is saved in JSON format at `~/.config/rpi-touch-demo/config.json`:

```json
{
  "header_title": "Raspberry Pi's new 10-inch Touch Display 2",
  "header_subtitle": "1200×1920 • 10-Point Multi-Touch Capacitive Display",
  "idle_cta_text": "TOUCH THE SCREEN WITH UP TO 10 FINGERS",
  "hud_touch_label": "TOUCH POINTS",
  "hud_mode_idle_text": "MODE: DEMO IDLE",
  "hud_mode_interactive_text": "MODE: MULTI-TOUCH INTERACTIVE",
  "touch_badge_label": "FINGER #{slot} ({x}, {y})",
  "primary_logo": "MFH.png",
  "active_logos": [
    "MFH.png",
    "logo.png"
  ],
  "logo_scales": {
    "MFH.png": 1.0,
    "logo.png": 1.0
  },
  "idle_timeout_seconds": 4.0,
  "admin_port": 8080
}
```

---

## 🔍 Troubleshooting & Maintenance

* **Check Service Status**:
  ```bash
  systemctl --user status rpi-touch-demo.service
  ```

* **View Real-Time Logs**:
  ```bash
  journalctl --user-unit=rpi-touch-demo.service -f
  ```

* **Restart Demo Service**:
  ```bash
  systemctl --user restart rpi-touch-demo.service
  ```

* **Stop Demo Service**:
  ```bash
  systemctl --user stop rpi-touch-demo.service
  ```

---

## 📄 License

MIT License — free to use, modify, and distribute for Raspberry Pi demonstrations and showcase displays.
