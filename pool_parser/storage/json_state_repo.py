from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any


class JsonStateRepository:
    def __init__(self, path: str = ".state/parser_state.json") -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()

    async def get_last_slot(self) -> int | None:
        async with self._lock:
            if not self._path.exists():
                return None
            try:
                raw = self._path.read_text(encoding="utf-8")
                payload: dict[str, Any] = json.loads(raw)
                slot = payload.get("last_slot")
                return slot if isinstance(slot, int) else None
            except (OSError, json.JSONDecodeError):
                return None

    async def store_last_slot(self, slot: int) -> None:
        async with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"last_slot": slot}
            self._path.write_text(json.dumps(payload), encoding="utf-8")

