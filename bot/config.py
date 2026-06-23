from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from bot.dates import parse_deadline

BOOKING_URL = (
    "https://formulieren.amsterdam.nl/TriplEforms/DirectRegelen/"
    "formulier/nl-NL/evAmsterdam/Afspraakmaken.aspx"
)

LOCATIONS: dict[str, str] = {
    "Centrum": "0f48f145-8bf6-4552-8cdc-fe77865d84d2",
    "Oost": "df7c3c3d-ed15-40d4-b412-8ae9e5ac8346",
    "West": "ae0b6c49-b217-4654-a92a-4a2bca2b0e63",
    "Nieuw-West": "7ea3914c-998a-4571-bb56-b48df3d13189",
    "Zuid": "ce47819f-bdc8-486c-b0ef-9e830fb85f9b",
    "Noord": "ec15f49f-1672-4b0f-9fb3-81f3c42e97d3",
    "Zuidoost": "18cdcf1d-e0be-4741-80ef-aac6dfd42ad5",
}

FOREIGN_BIRTH_CERT_SUBPRODUCT = "9cc273f2-6033-401f-8387-74aaaaa65a32"


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    state_file: Path
    headless: bool
    document_count: str
    notify_on_errors: bool
    deadline: date

    @classmethod
    def from_env(cls) -> Settings:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            raise ValueError(
                "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment or .env file."
            )

        deadline_raw = os.environ.get("DEADLINE_DATE", "2026-08-07").strip()

        return cls(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            state_file=Path(os.environ.get("STATE_FILE", "state.json")),
            headless=os.environ.get("HEADLESS", "true").lower() != "false",
            document_count=os.environ.get("DOCUMENT_COUNT", "1"),
            notify_on_errors=os.environ.get("NOTIFY_ON_ERRORS", "true").lower() != "false",
            deadline=parse_deadline(deadline_raw),
        )
