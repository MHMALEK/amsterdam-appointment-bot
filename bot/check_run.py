from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from bot.checker import AppointmentSlot
from bot.config import Settings
from bot.notify import format_soonest_message, send_telegram
from bot.state import SoonestState, load_state, save_state

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    notified: bool
    message: str | None = None
    soonest: datetime | None = None
    location: str | None = None
    slots_checked: int = 0


def pick_soonest(slots: list[AppointmentSlot]) -> AppointmentSlot | None:
    if not slots:
        return None
    return min(slots, key=lambda slot: slot.when)


def process_check(settings: Settings, slots: list[AppointmentSlot]) -> CheckResult:
    soonest_slot = pick_soonest(slots)
    state = load_state(settings.state_file)

    if soonest_slot is None:
        logger.info("No appointments before %s", settings.deadline)
        return CheckResult(notified=False, slots_checked=len(slots))

    should_notify = state.soonest is None or soonest_slot.when < state.soonest

    if should_notify:
        message = format_soonest_message(
            soonest_slot.when,
            soonest_slot.location,
            settings.deadline,
            state.soonest,
        )
        send_telegram(settings, message)
        save_state(
            settings.state_file,
            SoonestState(soonest=soonest_slot.when, location=soonest_slot.location),
        )
        logger.info(
            "Notified soonest slot: %s at %s",
            soonest_slot.when.isoformat(),
            soonest_slot.location,
        )
        return CheckResult(
            notified=True,
            message=message,
            soonest=soonest_slot.when,
            location=soonest_slot.location,
            slots_checked=len(slots),
        )

    logger.info(
        "Current best unchanged: %s at %s (checked %s slot(s))",
        state.soonest.isoformat() if state.soonest else "none",
        state.location,
        len(slots),
    )
    return CheckResult(
        notified=False,
        soonest=state.soonest,
        location=state.location,
        slots_checked=len(slots),
    )
