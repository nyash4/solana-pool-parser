from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from pool_parser.adapters.pumpfun.constants import PUMP_AMM_PROGRAM_ID

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_MAP = {c: i for i, c in enumerate(_B58_ALPHABET)}
PUMP_AMM_CREATE_POOL_DISCRIMINATOR = bytes([233, 146, 209, 142, 207, 104, 64, 188])


@dataclass(slots=True)
class JupiterPoolDetails:
    pool_address: str
    token_a: str
    token_b: str
    source_program: str


def looks_like_jupiter_new_pool_candidate(logs: list[str]) -> bool:
    names = _extract_instruction_names(logs)
    route_ops = {
        "route",
        "routev2",
        "exactoutroute",
        "sharedaccountsroute",
        "sharedaccountsroutev2",
    }
    has_route = any(name in route_ops for name in names)
    has_create_pool = "createpool" in names
    return has_route and has_create_pool


def extract_routed_pool_details(tx_result: dict[str, Any] | None) -> JupiterPoolDetails | None:
    if not tx_result:
        return None

    instruction_views = _collect_instruction_views(tx_result)
    for program_id, accounts, data in instruction_views:
        # PumpSwap instructions include: pool=0, base_mint=3, quote_mint=4
        if (
            program_id == PUMP_AMM_PROGRAM_ID
            and len(accounts) >= 5
            and data.startswith(PUMP_AMM_CREATE_POOL_DISCRIMINATOR)
        ):
            return JupiterPoolDetails(
                pool_address=accounts[0],
                token_a=accounts[3],
                token_b=accounts[4],
                source_program=program_id,
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
