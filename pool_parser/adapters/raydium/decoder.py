from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pool_parser.adapters.raydium.constants import RAYDIUM_INIT_LOG_HINTS


@dataclass(slots=True)
class RaydiumPoolDetails:
    pool_address: str | None
    token_a: str | None
    token_b: str | None
    fee_bps: int | None


def looks_like_pool_init(logs: list[str]) -> bool:
    lowered_logs = [line.lower() for line in logs]
    return any(hint in line for hint in RAYDIUM_INIT_LOG_HINTS for line in lowered_logs)


def extract_pool_details(tx_result: dict[str, Any] | None) -> RaydiumPoolDetails:
    if not tx_result:
        return RaydiumPoolDetails(None, None, None, None)

    meta = tx_result.get("meta") or {}
    post_balances = meta.get("postTokenBalances") or []

    token_a = None
    token_b = None
    if len(post_balances) >= 2:
        token_a = post_balances[0].get("mint")
        token_b = post_balances[1].get("mint")

    # Best-effort pool candidate: first writable account in message.
    pool_address = None
    tx = tx_result.get("transaction") or {}
    message = tx.get("message") or {}
    account_keys = message.get("accountKeys") or []
    for account in account_keys:
        if isinstance(account, dict) and account.get("writable"):
            pool_address = account.get("pubkey")
            if isinstance(pool_address, str):
                break

    return RaydiumPoolDetails(
        pool_address=pool_address if isinstance(pool_address, str) else None,
        token_a=token_a if isinstance(token_a, str) else None,
        token_b=token_b if isinstance(token_b, str) else None,
        fee_bps=None,
    )

