# Amsterdam appointment bot

Monitors Amsterdam gemeente appointment availability for **Buitenlandse akten inleveren** (foreign birth certificate registration in the BRP) across all Amsterdam Stadsloket offices except Weesp.

Sends Telegram notifications when new slots appear.

## Telegram setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
2. Message [@userinfobot](https://t.me/userinfobot) → copy your chat id.
3. Start a chat with your new bot (press **Start**) so it can message you.

## VPS deploy (Debian/Ubuntu)

Copy the project to your VPS, then:

```bash
cd amsterdam-appointment-bot
cp .env.example .env
nano .env   # add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
chmod +x deploy/install.sh
./deploy/install.sh
```

Test manually:

```bash
sudo -u amsterdam-bot /opt/amsterdam-appointment-bot/.venv/bin/python /opt/amsterdam-appointment-bot/check.py
```

The systemd timer runs every **10 minutes**. Logs:

```bash
journalctl -u amsterdam-appointment.service -f
```

## Local test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # fill in Telegram credentials
python check.py
```

## Offices checked

Centrum, Oost, West, Nieuw-West, Zuid, Noord, Zuidoost (Weesp excluded).

## Reset notifications

Delete `state.json` to get notified again about slots you've already been alerted for.
