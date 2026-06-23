#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/amsterdam-appointment-bot}"
APP_USER="${APP_USER:-amsterdam-bot}"

echo "==> Installing system packages (Debian/Ubuntu)"
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git \
  libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 libasound2

if ! id "$APP_USER" &>/dev/null; then
  echo "==> Creating user $APP_USER"
  sudo useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
fi

echo "==> Syncing app to $APP_DIR"
sudo mkdir -p "$APP_DIR"
sudo rsync -a --delete \
  --exclude .venv \
  --exclude state.json \
  --exclude .env \
  ./ "$APP_DIR/"

echo "==> Creating virtualenv"
sudo python3 -m venv "$APP_DIR/.venv"
sudo "$APP_DIR/.venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo "$APP_DIR/.venv/bin/playwright" install chromium
sudo "$APP_DIR/.venv/bin/playwright" install-deps chromium

if [ ! -f "$APP_DIR/.env" ]; then
  echo "==> Creating .env from example — edit it with your Telegram credentials"
  sudo cp "$APP_DIR/.env.example" "$APP_DIR/.env"
fi

sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "==> Installing systemd units"
sudo cp deploy/amsterdam-appointment.service /etc/systemd/system/
sudo cp deploy/amsterdam-appointment.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now amsterdam-appointment.timer

echo
echo "Done. Next steps:"
echo "  1. Edit $APP_DIR/.env with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
echo "  2. Test once: sudo -u $APP_USER $APP_DIR/.venv/bin/python $APP_DIR/check.py"
echo "  3. Watch logs: journalctl -u amsterdam-appointment.service -f"
