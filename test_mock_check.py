from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from bot.check_run import process_check
from bot.config import Settings
from bot.mock import make_mock_slot

MOCK_STATE_FILE = Path("state.mock.json")

FIRST_SLOT = datetime(2026, 7, 15, 10, 0)
EARLIER_SLOT = datetime(2026, 6, 20, 14, 0)


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def reset_mock_state() -> None:
    if MOCK_STATE_FILE.exists():
        MOCK_STATE_FILE.unlink()


def run_phase(label: str, slots: list, settings: Settings) -> tuple[bool, str | None]:
    print(f"\n--- {label} ---")
    result = process_check(settings, slots)
    if result.notified:
        print("Result: NOTIFIED (Telegram message sent)")
        assert result.message is not None
        print(f"Headline: {result.message.splitlines()[0]}")
    else:
        print("Result: no notification (state unchanged or no slots)")
    return result.notified, result.message


def main() -> int:
    load_dotenv()
    os.environ["STATE_FILE"] = str(MOCK_STATE_FILE)

    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    reset_mock_state()
    print(f"Mock test using {MOCK_STATE_FILE} and deadline {settings.deadline}")

    slot_a = make_mock_slot(FIRST_SLOT)
    slot_b = make_mock_slot(EARLIER_SLOT)

    failures: list[str] = []

    notified, message = run_phase("Phase 1: first discovery", [slot_a], settings)
    if not notified:
        failures.append("Phase 1 should notify on first slot")
    elif message and "Amsterdam appointment found before your deadline!" not in message:
        failures.append("Phase 1 message missing first-discovery headline")

    notified, _ = run_phase("Phase 2: same slot again", [slot_a], settings)
    if notified:
        failures.append("Phase 2 should NOT notify when slot is unchanged")

    notified, message = run_phase("Phase 3: earlier slot", [slot_b], settings)
    if not notified:
        failures.append("Phase 3 should notify when an earlier slot appears")
    elif message and "Earlier appointment found!" not in message:
        failures.append("Phase 3 message missing earlier-slot headline")

    print()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("All mock check phases passed.")
    print("Telegram messages were sent for phases 1 and 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
