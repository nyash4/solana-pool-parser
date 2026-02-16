from __future__ import annotations

import asyncio
import logging

from pool_parser.adapters.registry import build_adapters
from pool_parser.config.settings import Settings
from pool_parser.connectors.solana_rpc import SolanaRpcClient
from pool_parser.connectors.solana_ws import SolanaWsConnector
from pool_parser.core.pipeline import ParserPipeline
from pool_parser.notifier.stdout import StdoutNotifier
from pool_parser.storage.in_memory_repo import InMemoryPoolRepository
from pool_parser.storage.json_state_repo import JsonStateRepository


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


async def main() -> None:
    settings = Settings.from_env()
    setup_logging(settings.log_level)

    rpc_client = SolanaRpcClient(settings.solana_rpc_url)
    connector = SolanaWsConnector(settings.solana_ws_url)
    adapters = build_adapters(
        settings.enabled_adapters,
        rpc_client=rpc_client,
        max_tx_age_sec=settings.max_tx_age_sec,
    )

    pipeline = ParserPipeline(
        connector=connector,
        adapters=adapters,
        pool_repo=InMemoryPoolRepository(),
        state_repo=JsonStateRepository(settings.state_path),
        notifier=StdoutNotifier(),
    )
    await pipeline.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
