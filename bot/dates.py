from __future__ import annotations

import re
from datetime import date, datetime, timedelta

DUTCH_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}


def parse_month_label(label: str) -> tuple[int, int]:
    match = re.search(
        r"(januari|februari|maart|april|mei|juni|juli|augustus|"
        r"september|oktober|november|december)\s+(\d{4})",
        label,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Cannot parse month label: {label!r}")
    month_name = match.group(1).lower()
    year = int(match.group(2))
    return year, DUTCH_MONTHS[month_name]


def parse_deadline(value: str) -> date:
    year, month, day = (int(part) for part in value.split("-"))
    return date(year, month, day)


def calendar_grid_dates(year: int, month: int) -> list[date]:
    """Return the 42 dates shown in a Monday-first calendar grid for *month*."""
    first = date(year, month, 1)
    grid_start = first - timedelta(days=first.isoweekday() - 1)
    return [grid_start + timedelta(days=offset) for offset in range(42)]


def month_label_for_date(value: date) -> str:
    month_names = {index: name for name, index in DUTCH_MONTHS.items()}
    return f"{month_names[value.month]} {value.year}"


def slot_datetime(month_label: str, day: str, time_str: str) -> datetime:
    year, month = parse_month_label(month_label)
    hour, minute = (int(part) for part in time_str.split(":"))
    return datetime(year, month, int(day), hour, minute)


def slot_datetime_from_date(slot_date: date, time_str: str) -> datetime:
    hour, minute = (int(part) for part in time_str.split(":"))
    return datetime(slot_date.year, slot_date.month, slot_date.day, hour, minute)


def format_slot_datetime(value: datetime) -> str:
    month_names = {index: name for name, index in DUTCH_MONTHS.items()}
    return f"{value.day} {month_names[value.month]} {value.year} {value.strftime('%H:%M')}"
