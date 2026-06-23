from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from bot.check_run import process_check
from bot.checker import check_all_locations
from bot.config import Settings
from bot.mock import default_mock_slots
from bot.notify import send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

MOCK_STATE_FILE = "state.mock.json"


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
    parser = argparse.ArgumentParser(description="Check Amsterdam appointment availability.")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run notification logic with mock slots (uses state.mock.json, no Playwright).",
    )
    args = parser.parse_args()

    load_dotenv()

    if args.mock:
        os.environ["STATE_FILE"] = MOCK_STATE_FILE

    try:
        settings = Settings.from_env()
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    try:
        if args.mock:
            slots = default_mock_slots()
            logger.info("Mock mode: using %s slot(s), state file %s", len(slots), settings.state_file)
        else:
            slots = asyncio.run(check_all_locations(settings))
    except Exception as exc:
        logger.exception("Checker failed")
        if settings.notify_on_errors:
            send_telegram(
                settings,
                f"Amsterdam appointment checker failed:\n{exc}",
            )
        return 1

    process_check(settings, slots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
