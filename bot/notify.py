from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

from bot.config import BOOKING_URL, Settings
from bot.dates import format_slot_datetime


def send_telegram(settings: Settings, message: str) -> None:
    payload = urllib.parse.urlencode(
        {
            "chat_id": settings.telegram_chat_id,
            "text": message,
            "disable_web_page_preview": "false",
        }
    ).encode("utf-8")
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    request = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"Telegram API returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API error: {body}") from exc


def format_soonest_message(
    soonest_when: datetime,
    location: str,
    deadline: date,
    previous: datetime | None,
) -> str:
    formatted = format_slot_datetime(soonest_when)
    deadline_text = deadline.strftime("%d %B %Y")

    if previous is None:
        headline = "Amsterdam appointment found before your deadline!"
    else:
        headline = "Earlier appointment found!"

    lines = [
        headline,
        "Service: Buitenlandse akten inleveren (foreign birth certificate)",
        f"Deadline: before {deadline_text}",
        "",
        f"Soonest: {formatted}",
        f"Location: {location}",
    ]

    if previous is not None:
        lines.append(f"Previous best: {format_slot_datetime(previous)}")

    lines.extend(["", f"Book now: {BOOKING_URL}"])
    return "\n".join(lines)


def format_test_message(deadline: date) -> str:
    return (
        "Amsterdam appointment bot test OK.\n"
        f"Monitoring foreign birth certificate slots before {deadline.strftime('%d %B %Y')}.\n"
        "You will only be notified when a sooner appointment is found."
    )
