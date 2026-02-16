from __future__ import annotations

from typing import Sequence

from pool_parser.adapters.raydium.constants import RAYDIUM_PROGRAM_IDS
from pool_parser.adapters.raydium.decoder import extract_pool_details, looks_like_pool_init
from pool_parser.connectors.solana_rpc import SolanaRpcClient
from pool_parser.core.models import PoolEvent, RawEvent
from pool_parser.core.tx_filters import is_tx_fresh


class RaydiumAdapter:
    name = "raydium"

    def __init__(
        self,
        rpc_client: SolanaRpcClient | None = None,
        max_tx_age_sec: int | None = 1800,
    ) -> None:
        self._rpc_client = rpc_client
        self._max_tx_age_sec = max_tx_age_sec

    def program_ids(self) -> Sequence[str]:
        return RAYDIUM_PROGRAM_IDS

    async def parse_new_pool(self, raw_event: RawEvent) -> PoolEvent | None:
        logs = raw_event.payload.get("logs") or []
        if not isinstance(logs, list) or not all(isinstance(line, str) for line in logs):
            return None

        if not looks_like_pool_init(logs):
            return None

        tx_result = None
        if self._rpc_client is not None:
            tx_result = await self._rpc_client.get_transaction(raw_event.signature)
            if tx_result is not None and not is_tx_fresh(tx_result, self._max_tx_age_sec):
                return None

        details = extract_pool_details(tx_result)
        pool_address = details.pool_address or f"unknown:{raw_event.signature}"
        token_a = details.token_a or "UNKNOWN"
        token_b = details.token_b or "UNKNOWN"

        return PoolEvent(
            aggregator=self.name,
            pool_address=pool_address,
            token_a=token_a,
            token_b=token_b,
            fee_bps=details.fee_bps,
            created_slot=raw_event.slot,
            signature=raw_event.signature,
            raw=raw_event.payload,
        )
