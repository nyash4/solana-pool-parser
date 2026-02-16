from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from pool_parser.adapters.meteora.constants import (
    ALL_INIT_INSTRUCTION_NAMES,
    DAMM_V2_INIT_ACCOUNT_LAYOUTS,
    DAMM_V2_INIT_DISCRIMINATORS,
    DLMM_INIT_ACCOUNT_LAYOUTS,
    DLMM_INIT_DISCRIMINATORS,
    METEORA_DAMM_V2_PROGRAM_ID,
    METEORA_DLMM_PROGRAM_ID,
)

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_MAP = {c: i for i, c in enumerate(_B58_ALPHABET)}


@dataclass(slots=True)
class MeteoraPoolDetails:
    pool_address: str
    token_a: str
    token_b: str
    pool_type: str
    instruction_name: str


def looks_like_meteora_new_pool(logs: list[str]) -> bool:
    names = _extract_instruction_names(logs)
    normalized_targets = {name.replace("_", "") for name in ALL_INIT_INSTRUCTION_NAMES}
    return any(name in normalized_targets for name in names)


def extract_pool_details(tx_result: dict[str, Any] | None) -> MeteoraPoolDetails | None:
    if not tx_result:
        return None

    for view in _collect_instruction_views(tx_result):
        details = _parse_damm_v2(view)
        if details is not None:
            return details

        details = _parse_dlmm(view)
        if details is not None:
            return details

    return None


def _parse_damm_v2(view: tuple[str, list[str], bytes]) -> MeteoraPoolDetails | None:
    program_id, accounts, data = view
    if program_id != METEORA_DAMM_V2_PROGRAM_ID:
        return None

    for instruction_name, discriminator in DAMM_V2_INIT_DISCRIMINATORS.items():
        if data.startswith(discriminator):
            layout = DAMM_V2_INIT_ACCOUNT_LAYOUTS.get(instruction_name)
            if layout is None:
                return None
            pool_idx, token_a_idx, token_b_idx = layout
            if max(pool_idx, token_a_idx, token_b_idx) >= len(accounts):
                return None
            return MeteoraPoolDetails(
                pool_address=accounts[pool_idx],
                token_a=accounts[token_a_idx],
                token_b=accounts[token_b_idx],
                pool_type="damm_v2",
                instruction_name=instruction_name,
            )
    return None


def _parse_dlmm(view: tuple[str, list[str], bytes]) -> MeteoraPoolDetails | None:
    program_id, accounts, data = view
    if program_id != METEORA_DLMM_PROGRAM_ID:
        return None

    for instruction_name, discriminator in DLMM_INIT_DISCRIMINATORS.items():
        if data.startswith(discriminator):
            layout = DLMM_INIT_ACCOUNT_LAYOUTS.get(instruction_name)
            if layout is None:
                return None
            pool_idx, token_a_idx, token_b_idx = layout
            if max(pool_idx, token_a_idx, token_b_idx) >= len(accounts):
                return None
            return MeteoraPoolDetails(
                pool_address=accounts[pool_idx],
                token_a=accounts[token_a_idx],
                token_b=accounts[token_b_idx],
                pool_type="dlmm",
                instruction_name=instruction_name,
            )
    return None


def _collect_instruction_views(tx_result: dict[str, Any]) -> list[tuple[str, list[str], bytes]]:
    tx = tx_result.get("transaction") or {}
    message = tx.get("message") or {}
    account_keys = message.get("accountKeys") or []
    outer_instructions = message.get("instructions") or []
    meta = tx_result.get("meta") or {}
    inner_groups = meta.get("innerInstructions") or []

    views: list[tuple[str, list[str], bytes]] = []
    for instruction in outer_instructions:
        view = _to_instruction_view(instruction, account_keys)
        if view is not None:
            views.append(view)

    for group in inner_groups:
        for instruction in group.get("instructions") or []:
            view = _to_instruction_view(instruction, account_keys)
            if view is not None:
                views.append(view)

    return views


def _to_instruction_view(
    instruction: dict[str, Any],
    account_keys: list[Any],
) -> tuple[str, list[str], bytes] | None:
    program_id = _resolve_program_id(instruction, account_keys)
    if program_id is None:
        return None
    accounts = _resolve_accounts(instruction, account_keys)
    data = _resolve_data(instruction)
    return program_id, accounts, data


def _resolve_program_id(instruction: dict[str, Any], account_keys: list[Any]) -> str | None:
    direct = instruction.get("programId")
    if isinstance(direct, str):
        return direct

    index = instruction.get("programIdIndex")
    if not isinstance(index, int):
        return None
    return _account_key_by_index(account_keys, index)


def _resolve_accounts(instruction: dict[str, Any], account_keys: list[Any]) -> list[str]:
    raw_accounts = instruction.get("accounts") or []
    normalized: list[str] = []
    for entry in raw_accounts:
        if isinstance(entry, str):
            normalized.append(entry)
            continue
        if isinstance(entry, int):
            key = _account_key_by_index(account_keys, entry)
            if key:
                normalized.append(key)
    return normalized


def _resolve_data(instruction: dict[str, Any]) -> bytes:
    raw = instruction.get("data")
    if not isinstance(raw, str) or not raw:
        return b""
    return _b58decode(raw)


def _account_key_by_index(account_keys: list[Any], index: int) -> str | None:
    if index < 0 or index >= len(account_keys):
        return None
    item = account_keys[index]
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        pubkey = item.get("pubkey")
        return pubkey if isinstance(pubkey, str) else None
    return None


def _extract_instruction_names(logs: list[str]) -> set[str]:
    names: set[str] = set()
    pattern = re.compile(r"instruction:\s*([a-zA-Z0-9_]+)", re.IGNORECASE)
    for line in logs:
        match = pattern.search(line)
        if not match:
            continue
        normalized = match.group(1).lower().replace("_", "")
        names.add(normalized)
    return names


def _b58decode(value: str) -> bytes:
    num = 0
    try:
        for ch in value:
            num = num * 58 + _B58_MAP[ch]
    except KeyError:
        return b""

    decoded = b""
    while num > 0:
        num, rem = divmod(num, 256)
        decoded = bytes([rem]) + decoded

    leading_zeros = 0
    for ch in value:
        if ch == "1":
            leading_zeros += 1
        else:
            break
    return b"\x00" * leading_zeros + decoded
