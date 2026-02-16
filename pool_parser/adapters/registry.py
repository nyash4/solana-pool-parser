from __future__ import annotations

from pool_parser.adapters.jupiter.adapter import JupiterAdapter
from pool_parser.adapters.meteora.adapter import MeteoraAdapter
from pool_parser.adapters.pumpfun.adapter import PumpfunAdapter
from pool_parser.adapters.raydium.adapter import RaydiumAdapter
from pool_parser.connectors.solana_rpc import SolanaRpcClient
from pool_parser.core.interfaces import PoolAdapter


def build_adapters(
    enabled_adapters: tuple[str, ...],
    rpc_client: SolanaRpcClient,
    max_tx_age_sec: int,
) -> list[PoolAdapter]:
    adapters: list[PoolAdapter] = []
    for name in enabled_adapters:
        if name == "raydium":
            adapters.append(RaydiumAdapter(rpc_client=rpc_client, max_tx_age_sec=max_tx_age_sec))
            continue
        if name == "pumpfun":
            adapters.append(PumpfunAdapter(rpc_client=rpc_client, max_tx_age_sec=max_tx_age_sec))
            continue
        if name == "jupiter":
            adapters.append(JupiterAdapter(rpc_client=rpc_client, max_tx_age_sec=max_tx_age_sec))
            continue
        if name == "meteora":
            adapters.append(MeteoraAdapter(rpc_client=rpc_client, max_tx_age_sec=max_tx_age_sec))
            continue
        raise ValueError(f"Unknown adapter: {name}")

    if not adapters:
        raise ValueError("No adapters enabled")
    return adapters
