from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    solana_ws_url: str
    solana_rpc_url: str
    log_level: str = "INFO"
    state_path: str = ".state/parser_state.json"
    enabled_adapters: tuple[str, ...] = ("raydium",)
    max_tx_age_sec: int = 1800

    @classmethod
    def from_env(cls) -> "Settings":
        ws_url = os.getenv("SOLANA_WS_URL", "")
        rpc_url = os.getenv("SOLANA_RPC_URL", "")
        if not ws_url or not rpc_url:
            raise ValueError("Set SOLANA_WS_URL and SOLANA_RPC_URL environment variables")
        return cls(
            solana_ws_url=ws_url,
            solana_rpc_url=rpc_url,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            state_path=os.getenv("STATE_PATH", ".state/parser_state.json"),
            enabled_adapters=tuple(
                item.strip().lower()
                for item in os.getenv("ENABLED_ADAPTERS", "raydium").split(",")
                if item.strip()
            ),
            max_tx_age_sec=int(os.getenv("MAX_TX_AGE_SEC", "1800")),
        )
