from __future__ import annotations

from datetime import datetime

from bot.checker import AppointmentSlot

DUTCH_MONTHS = (
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
)


def make_mock_slot(
    when: datetime,
    location: str = "Centrum",
) -> AppointmentSlot:
    month_label = f"{DUTCH_MONTHS[when.month - 1]} {when.year}"
    return AppointmentSlot(
        when=when,
        location=location,
        month_label=month_label,
        day=str(when.day),
        time=when.strftime("%H:%M"),
    )


def default_mock_slots() -> list[AppointmentSlot]:
    return [make_mock_slot(datetime(2026, 7, 15, 10, 0))]
