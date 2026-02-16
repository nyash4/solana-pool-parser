from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class RawEvent:
    signature: str
    slot: int
    program_id: str
    payload: dict[str, Any]
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class PoolEvent:
    aggregator: str
    pool_address: str
    token_a: str
    token_b: str
    fee_bps: int | None
    created_slot: int
    signature: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = field(default_factory=dict)

