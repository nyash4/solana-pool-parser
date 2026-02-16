from __future__ import annotations

# Keep this list up-to-date with Raydium program versions you want to monitor.
# These are placeholders and should be verified for your exact target pools.
RAYDIUM_PROGRAM_IDS: tuple[str, ...] = (
    "675kPX9MHTjS2zt1qfr1NYHuzef8f4VxT6Hkq8w4Tg6",  # AMM v4 (commonly used)
)

RAYDIUM_INIT_LOG_HINTS: tuple[str, ...] = (
    "initialize",
    "initialize2",
    "init_pc_amount",
    "create_pool",
)

