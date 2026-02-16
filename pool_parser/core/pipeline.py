from __future__ import annotations

import logging
from typing import Sequence

from pool_parser.core.interfaces import (
    EventConnector,
    Notifier,
    PoolAdapter,
    PoolRepository,
    StateRepository,
)
from pool_parser.core.models import RawEvent
from pool_parser.core.router import EventRouter

logger = logging.getLogger(__name__)


class ParserPipeline:
    def __init__(
        self,
        connector: EventConnector,
        adapters: Sequence[PoolAdapter],
        pool_repo: PoolRepository,
        state_repo: StateRepository,
        notifier: Notifier,
    ) -> None:
        self._connector = connector
        self._adapters = list(adapters)
        self._pool_repo = pool_repo
        self._state_repo = state_repo
        self._notifier = notifier
        self._router = EventRouter(self._adapters)

    async def run_forever(self) -> None:
        program_ids = self._collect_program_ids(self._adapters)
        start_slot = await self._state_repo.get_last_slot()

        logger.info(
            "Starting parser pipeline: adapters=%s program_ids=%d start_slot=%s",
            [a.name for a in self._adapters],
            len(program_ids),
            start_slot,
        )

        async for raw_event in self._connector.stream(program_ids=program_ids, start_slot=start_slot):
            await self._handle_event(raw_event)

    async def _handle_event(self, raw_event: RawEvent) -> None:
        if await self._pool_repo.is_signature_processed(raw_event.signature):
            return

        routed_adapters = self._router.route(raw_event)
        for adapter in routed_adapters:
            try:
                pool_event = await adapter.parse_new_pool(raw_event)
            except Exception:
                logger.exception(
                    "Adapter error: adapter=%s signature=%s slot=%s",
                    adapter.name,
                    raw_event.signature,
                    raw_event.slot,
                )
                continue

            if pool_event is None:
                continue

            is_new = await self._pool_repo.save_pool_if_new(pool_event)
            if is_new:
                await self._notifier.notify_new_pool(pool_event)

        await self._pool_repo.mark_signature_processed(raw_event.signature)
        await self._state_repo.store_last_slot(raw_event.slot)

    @staticmethod
    def _collect_program_ids(adapters: Sequence[PoolAdapter]) -> list[str]:
        ids: set[str] = set()
        for adapter in adapters:
            for program_id in adapter.program_ids():
                ids.add(program_id)
        return sorted(ids)

