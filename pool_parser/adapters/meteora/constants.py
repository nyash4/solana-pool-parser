from __future__ import annotations

# Official SDK sources:
# - dlmm-sdk: LBCLMM_PROGRAM_IDS mainnet-beta
# - damm-v2-sdk: CP_AMM_PROGRAM_ID
METEORA_DLMM_PROGRAM_ID = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
METEORA_DAMM_V2_PROGRAM_ID = "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

METEORA_PROGRAM_IDS: tuple[str, ...] = (
    METEORA_DLMM_PROGRAM_ID,
    METEORA_DAMM_V2_PROGRAM_ID,
)

# Discriminators from official IDLs.
DAMM_V2_INIT_DISCRIMINATORS: dict[str, bytes] = {
    "initialize_pool": bytes([95, 180, 10, 172, 84, 174, 232, 40]),
    "initialize_customizable_pool": bytes([20, 161, 241, 24, 189, 221, 180, 2]),
    "initialize_pool_with_dynamic_config": bytes([149, 82, 72, 197, 253, 252, 68, 15]),
}

DLMM_INIT_DISCRIMINATORS: dict[str, bytes] = {
    "initialize_permission_lb_pair": bytes([108, 102, 213, 85, 251, 3, 53, 21]),
    "initialize_customizable_permissionless_lb_pair": bytes([46, 39, 41, 135, 111, 183, 200, 64]),
    "initialize_customizable_permissionless_lb_pair2": bytes([243, 73, 129, 126, 51, 19, 241, 107]),
    "initialize_lb_pair": bytes([45, 154, 237, 210, 221, 15, 166, 92]),
    "initialize_lb_pair2": bytes([73, 59, 36, 120, 237, 83, 108, 198]),
}

ALL_INIT_INSTRUCTION_NAMES: set[str] = {
    *DAMM_V2_INIT_DISCRIMINATORS.keys(),
    *DLMM_INIT_DISCRIMINATORS.keys(),
}

# instruction_name -> (pool_index, token_a_index, token_b_index)
DAMM_V2_INIT_ACCOUNT_LAYOUTS: dict[str, tuple[int, int, int]] = {
    "initialize_pool": (6, 8, 9),
    "initialize_customizable_pool": (5, 7, 8),
    "initialize_pool_with_dynamic_config": (7, 9, 10),
}

DLMM_INIT_ACCOUNT_LAYOUTS: dict[str, tuple[int, int, int]] = {
    "initialize_permission_lb_pair": (1, 3, 4),
    "initialize_customizable_permissionless_lb_pair": (0, 2, 3),
    "initialize_customizable_permissionless_lb_pair2": (0, 2, 3),
    "initialize_lb_pair": (0, 2, 3),
    "initialize_lb_pair2": (0, 2, 3),
}
