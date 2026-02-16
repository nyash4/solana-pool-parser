from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from pool_parser.core.interfaces import PoolAdapter
from pool_parser.core.models import RawEvent


class EventRouter:
    def __init__(self, adapters: Iterable[PoolAdapter]) -> None:
        self._adapters_by_program: dict[str, list[PoolAdapter]] = defaultdict(list)
        self._fallback_adapters: list[PoolAdapter] = []

        for adapter in adapters:
            ids = list(adapter.program_ids())
            if not ids:
                self._fallback_adapters.append(adapter)
                continue
            for program_id in ids:
                self._adapters_by_program[program_id].append(adapter)

    def route(self, raw_event: RawEvent) -> list[PoolAdapter]:
        direct = self._adapters_by_program.get(raw_event.program_id, [])
        if direct:
            return direct
        return self._fallback_adapters

