from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

from bot.config import BOOKING_URL, Settings


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


def format_availability_message(entries: list[dict]) -> str:
    lines = [
        "Amsterdam appointment available!",
        "Service: Buitenlandse akten inleveren (foreign birth certificate)",
        "",
    ]

    for entry in entries:
        location = entry["location"]
        month_label = entry["month_label"]
        days = entry["days"]
        sample_times = entry["sample_times"]

        lines.append(f"{location} ({month_label}):")
        lines.append(f"  Days: {', '.join(days[:10])}")
        if len(days) > 10:
            lines.append(f"  …and {len(days) - 10} more days")

        for day, times in list(sample_times.items())[:2]:
            lines.append(f"  {day}: {', '.join(times)}")
        lines.append("")

    lines.append(f"Book now: {BOOKING_URL}")
    return "\n".join(lines).strip()
