from __future__ import annotations

from typing import Sequence

from pool_parser.core.models import PoolEvent, RawEvent


class TemplateAdapter:
    """
    Copy this class when adding a new aggregator.
    """

    name = "template"

    def program_ids(self) -> Sequence[str]:
        # Return aggregator program ids you want to subscribe to.
        return ()

    async def parse_new_pool(self, raw_event: RawEvent) -> PoolEvent | None:
        # 1) Check that event matches pool creation pattern.
        # 2) Decode pool address + token mints + fee from tx/logs.
        # 3) Return PoolEvent when this is a new pool event.
        return None

