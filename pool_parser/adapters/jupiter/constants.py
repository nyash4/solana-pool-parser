from __future__ import annotations

from pool_parser.adapters.pumpfun.constants import PUMP_AMM_PROGRAM_ID

# Jupiter swap programs (v6 and legacy v4).
JUPITER_PROGRAM_IDS: tuple[str, ...] = (
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
)

# DEX programs currently decoded from Jupiter-routed tx.
SUPPORTED_SOURCE_PROGRAM_IDS: tuple[str, ...] = (
    PUMP_AMM_PROGRAM_ID,
)

