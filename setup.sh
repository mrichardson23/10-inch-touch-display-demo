#!/usr/bin/env bash
# ==============================================================================
# Raspberry Pi 10-Inch Touch Display 2 Native Demo — Automated Setup Script
# ==============================================================================

set -e

echo "----------------------------------------------------------------------"
echo "🍓 Installing Raspberry Pi 10-Inch Touch Display 2 Native Demo..."
echo "----------------------------------------------------------------------"

# 1. Determine target directory and user
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$(whoami)"

echo "[1/5] Setting up for user: $CURRENT_USER in $TARGET_DIR"

# 2. Update APT and install system dependencies
echo "[2/5] Installing system packages & dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-pygame \
    python3-flask \
    python3-evdev \
    python3-pil \
    chromium-browser \
    systemd

# 3. Add user to input group for hardware evdev access
echo "[3/5] Adding $CURRENT_USER to 'input' group for multi-touch & keyboard access..."
sudo usermod -aG input "$CURRENT_USER" || true

# 4. Create user config directory
CONFIG_DIR="$HOME/.config/rpi-touch-demo"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.json" ] && [ -f "$TARGET_DIR/config.json" ]; then
    cp "$TARGET_DIR/config.json" "$CONFIG_DIR/config.json"
    echo "      Copied initial config.json to $CONFIG_DIR/"
fi

# 5. Setup systemd user service for autostart
echo "[4/5] Configuring systemd user service..."
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

SERVICE_FILE="$SYSTEMD_USER_DIR/rpi-touch-demo.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Raspberry Pi 10-Inch Touch Display 2 Native Demo
After=graphical-session.target labwc.service

[Service]
Type=simple
Environment=PYTHONUNBUFFERED=1
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DISPLAY=:0
WorkingDirectory=$TARGET_DIR
ExecStart=/usr/bin/python3 $TARGET_DIR/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

# Enable linger so service starts on boot
loginctl enable-linger "$CURRENT_USER" || true

# Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable rpi-touch-demo.service

echo "[5/5] Service installed & enabled!"

echo "----------------------------------------------------------------------"
echo "✅ Setup Complete!"
echo "----------------------------------------------------------------------"
echo "To start the demo right now, run:"
echo "  systemctl --user start rpi-touch-demo.service"
echo ""
echo "To view live logs, run:"
echo "  journalctl --user-unit=rpi-touch-demo.service -f"
echo ""
echo "Web Admin Panel URL:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
echo "----------------------------------------------------------------------"
