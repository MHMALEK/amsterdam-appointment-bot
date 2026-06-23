from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SoonestState:
    soonest: datetime | None = None
    location: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> SoonestState:
        raw = data.get("soonest")
        if not raw:
            return cls()
        return cls(
            soonest=datetime.fromisoformat(raw["datetime"]),
            location=raw.get("location"),
        )

    def to_dict(self) -> dict:
        if self.soonest is None or self.location is None:
            return {"soonest": None}
        return {
            "soonest": {
                "datetime": self.soonest.isoformat(),
                "location": self.location,
            }
        }


def load_state(path: Path) -> SoonestState:
    if not path.exists():
        return SoonestState()
    data = json.loads(path.read_text(encoding="utf-8"))
    return SoonestState.from_dict(data)


def save_state(path: Path, state: SoonestState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
