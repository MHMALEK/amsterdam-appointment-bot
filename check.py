from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from bot.checker import check_all_locations
from bot.config import Settings
from bot.notify import format_availability_message, send_telegram
from bot.state import day_key, load_notified_keys, save_notified_keys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


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
        logger.error("%s", exc)
        return 1

    try:
        availabilities = asyncio.run(check_all_locations(settings))
    except Exception as exc:
        logger.exception("Checker failed")
        if settings.notify_on_errors:
            send_telegram(
                settings,
                f"Amsterdam appointment checker failed:\n{exc}",
            )
        return 1

    notified = load_notified_keys(settings.state_file)
    new_entries = []

    for availability in availabilities:
        new_days = [
            day
            for day in availability.days
            if day_key(availability.location, availability.month_label, day) not in notified
        ]
        if not new_days:
            continue

        for day in new_days:
            notified.add(day_key(availability.location, availability.month_label, day))

        new_entries.append(
            {
                "location": availability.location,
                "month_label": availability.month_label,
                "days": new_days,
                "sample_times": {
                    day: times
                    for day, times in availability.sample_times.items()
                    if day in new_days
                },
            }
        )

    if new_entries:
        message = format_availability_message(new_entries)
        send_telegram(settings, message)
        save_notified_keys(settings.state_file, notified)
        logger.info(
            "Sent Telegram notification for %s location(s) with new days",
            len(new_entries),
        )
    else:
        checked = len(availabilities)
        logger.info("No new availability (%s location(s) currently have slots)", checked)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
