from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from pool_parser.adapters.pumpfun.constants import PUMP_AMM_PROGRAM_ID, PUMP_PROGRAM_ID, SOL_MINT

EVENT_PUMP_CREATE = "pump_create"
EVENT_PUMP_CREATE_V2 = "pump_create_v2"
EVENT_PUMPSWAP_CREATE_POOL = "pumpswap_create_pool"


@dataclass(slots=True)
class PumpfunPoolDetails:
    pool_address: str | None
    token_a: str | None
    token_b: str | None
    fee_bps: int | None


def detect_event_kind(logs: list[str]) -> str | None:
    names = _extract_instruction_names(logs)
    if "createpool" in names:
        return EVENT_PUMPSWAP_CREATE_POOL
    if "createv2" in names:
        return EVENT_PUMP_CREATE_V2
    if "create" in names:
        return EVENT_PUMP_CREATE
    return None


def detect_event_kind_for_program(logs: list[str], program_id: str) -> str | None:
    names = _extract_instruction_names(logs)

    if program_id == PUMP_AMM_PROGRAM_ID:
        if "createpool" in names:
            return EVENT_PUMPSWAP_CREATE_POOL
        return None

    if program_id == PUMP_PROGRAM_ID:
        if "createv2" in names:
            return EVENT_PUMP_CREATE_V2
        if "create" in names:
            return EVENT_PUMP_CREATE
        return None

    return None


def extract_pool_details(tx_result: dict[str, Any] | None, event_kind: str) -> PumpfunPoolDetails:
    if not tx_result:
        return PumpfunPoolDetails(None, None, None, None)

    instruction_views = _collect_instruction_views(tx_result)

    if event_kind in (EVENT_PUMP_CREATE, EVENT_PUMP_CREATE_V2):
        accounts = _find_instruction_accounts(instruction_views, PUMP_PROGRAM_ID, min_len=4)
        if not accounts:
            return PumpfunPoolDetails(None, None, SOL_MINT, None)
        # From pump IDL: mint=0, bonding_curve=2
        return PumpfunPoolDetails(
            pool_address=accounts[2],
            token_a=accounts[0],
            token_b=SOL_MINT,
            fee_bps=None,
        )

    if event_kind == EVENT_PUMPSWAP_CREATE_POOL:
        accounts = _find_instruction_accounts(instruction_views, PUMP_AMM_PROGRAM_ID, min_len=5)
        if not accounts:
            return PumpfunPoolDetails(None, None, None, None)
        # From pump_amm IDL: pool=0, base_mint=3, quote_mint=4
        return PumpfunPoolDetails(
            pool_address=accounts[0],
            token_a=accounts[3],
            token_b=accounts[4],
            fee_bps=None,
        )

    return PumpfunPoolDetails(None, None, None, None)


def _find_instruction_accounts(
    instruction_views: list[tuple[str, list[str]]],
    program_id: str,
    min_len: int,
) -> list[str] | None:
    for ins_program_id, accounts in instruction_views:
        if ins_program_id != program_id:
            continue
        if len(accounts) >= min_len:
            return accounts
    return None


def _collect_instruction_views(tx_result: dict[str, Any]) -> list[tuple[str, list[str]]]:
    tx = tx_result.get("transaction") or {}
    message = tx.get("message") or {}
    account_keys = message.get("accountKeys") or []
    outer_instructions = message.get("instructions") or []
    meta = tx_result.get("meta") or {}
    inner_groups = meta.get("innerInstructions") or []

    views: list[tuple[str, list[str]]] = []

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
) -> tuple[str, list[str]] | None:
    program_id = _resolve_program_id(instruction, account_keys)
    if program_id is None:
        return None
    accounts = _resolve_accounts(instruction, account_keys)
    return program_id, accounts


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
