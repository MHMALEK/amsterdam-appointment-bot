from __future__ import annotations

import os
import sys
from pathlib import Path

from bot.config import Settings
from bot.notify import format_test_message, send_telegram


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    load_dotenv()
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Add TELEGRAM_CHAT_ID to .env (get it from @userinfobot)", file=sys.stderr)
        return 1

    send_telegram(settings, format_test_message(settings.deadline))
    print("Test notification sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
