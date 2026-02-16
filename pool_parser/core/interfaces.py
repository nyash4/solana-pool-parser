from __future__ import annotations

from typing import AsyncIterator, Protocol, Sequence

from pool_parser.core.models import PoolEvent, RawEvent


class PoolAdapter(Protocol):
    name: str

    def program_ids(self) -> Sequence[str]:
        ...

    async def parse_new_pool(self, raw_event: RawEvent) -> PoolEvent | None:
        ...


class EventConnector(Protocol):
    async def stream(
        self,
        program_ids: Sequence[str],
        start_slot: int | None = None,
    ) -> AsyncIterator[RawEvent]:
        ...


class PoolRepository(Protocol):
    async def save_pool_if_new(self, pool: PoolEvent) -> bool:
        ...

    async def mark_signature_processed(self, signature: str) -> None:
        ...

    async def is_signature_processed(self, signature: str) -> bool:
        ...


class StateRepository(Protocol):
    async def get_last_slot(self) -> int | None:
        ...

    async def store_last_slot(self, slot: int) -> None:
        ...


class Notifier(Protocol):
    async def notify_new_pool(self, pool: PoolEvent) -> None:
        ...

