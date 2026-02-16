from __future__ import annotations

from pool_parser.core.models import PoolEvent


class InMemoryPoolRepository:
    def __init__(self) -> None:
        self._seen_pools: set[str] = set()
        self._seen_signatures: set[str] = set()
        self._items: list[PoolEvent] = []

    async def save_pool_if_new(self, pool: PoolEvent) -> bool:
        key = f"{pool.aggregator}:{pool.pool_address}"
        if key in self._seen_pools:
            return False
        self._seen_pools.add(key)
        self._items.append(pool)
        return True

    async def mark_signature_processed(self, signature: str) -> None:
        self._seen_signatures.add(signature)

    async def is_signature_processed(self, signature: str) -> bool:
        return signature in self._seen_signatures

    @property
    def items(self) -> list[PoolEvent]:
        return list(self._items)

