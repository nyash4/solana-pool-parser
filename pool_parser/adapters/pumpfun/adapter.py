from __future__ import annotations

import asyncio
import logging
from typing import Sequence

from pool_parser.adapters.pumpfun.constants import PUMPFUN_PROGRAM_IDS
from pool_parser.adapters.pumpfun.decoder import detect_event_kind_for_program, extract_pool_details
from pool_parser.connectors.solana_rpc import SolanaRpcClient
from pool_parser.core.models import PoolEvent, RawEvent
from pool_parser.core.tx_filters import is_tx_fresh

logger = logging.getLogger(__name__)


class PumpfunAdapter:
    name = "pumpfun"

    def __init__(
        self,
        rpc_client: SolanaRpcClient | None = None,
        max_tx_age_sec: int | None = 1800,
    ) -> None:
        self._rpc_client = rpc_client
        self._max_tx_age_sec = max_tx_age_sec

    def program_ids(self) -> Sequence[str]:
        return PUMPFUN_PROGRAM_IDS

    async def parse_new_pool(self, raw_event: RawEvent) -> PoolEvent | None:
        if raw_event.payload.get("err") is not None:
            return None

        logs = raw_event.payload.get("logs") or []
        if not isinstance(logs, list) or not all(isinstance(line, str) for line in logs):
            return None

        event_kind = detect_event_kind_for_program(logs, raw_event.program_id)
        if event_kind is None:
            return None

        tx_result = None
        if self._rpc_client is not None:
            tx_result = await self._fetch_tx_with_retries(raw_event.signature)
        if not tx_result:
            return None
        if not is_tx_fresh(tx_result, self._max_tx_age_sec):
            return None

        details = extract_pool_details(tx_result, event_kind)
        if not details.pool_address or not details.token_a or not details.token_b:
            return None

        raw_payload = dict(raw_event.payload)
        raw_payload["event_kind"] = event_kind

        return PoolEvent(
            aggregator=self.name,
            pool_address=details.pool_address,
            token_a=details.token_a,
            token_b=details.token_b,
            fee_bps=details.fee_bps,
            created_slot=raw_event.slot,
            signature=raw_event.signature,
            raw=raw_payload,
        )

    async def _fetch_tx_with_retries(self, signature: str) -> dict | None:
        assert self._rpc_client is not None
        delay_sec = 0.2
        for attempt in range(5):
            tx_result = await self._rpc_client.get_transaction(
                signature=signature,
                commitment="confirmed",
            )
            if tx_result is not None:
                return tx_result
            if attempt < 4:
                await asyncio.sleep(delay_sec)
                delay_sec *= 2

        logger.debug("Skipping tx without details after retries: %s", signature)
        return None
