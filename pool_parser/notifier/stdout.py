from __future__ import annotations

import json

from pool_parser.core.models import PoolEvent


class StdoutNotifier:
    async def notify_new_pool(self, pool: PoolEvent) -> None:
        payload = {
            "aggregator": pool.aggregator,
            "pool_address": pool.pool_address,
            "token_a": pool.token_a,
            "token_b": pool.token_b,
            "fee_bps": pool.fee_bps,
            "slot": pool.created_slot,
            "signature": pool.signature,
            "created_at": pool.created_at.isoformat(),
        }
        print(json.dumps(payload, ensure_ascii=False))

