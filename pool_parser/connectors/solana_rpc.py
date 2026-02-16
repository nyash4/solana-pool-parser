from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class SolanaRpcClient:
    def __init__(self, rpc_url: str, timeout_sec: float = 10.0) -> None:
        self._rpc_url = rpc_url
        self._timeout_sec = timeout_sec

    async def get_transaction(
        self,
        signature: str,
        commitment: str = "confirmed",
    ) -> dict[str, Any] | None:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {
                    "encoding": "jsonParsed",
                    "maxSupportedTransactionVersion": 0,
                    "commitment": commitment,
                },
            ],
        }
        return await asyncio.to_thread(self._post_json_rpc, payload)

    def _post_json_rpc(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        body = json.dumps(payload).encode("utf-8")
        req = Request(
            self._rpc_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self._timeout_sec) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw)
                return parsed.get("result")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            logger.exception("RPC request failed")
            return None
