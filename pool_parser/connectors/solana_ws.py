from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Sequence

from pool_parser.core.models import RawEvent

logger = logging.getLogger(__name__)


class SolanaWsConnector:
    def __init__(
        self,
        ws_url: str,
        commitment: str = "confirmed",
        reconnect_delay_sec: float = 2.0,
    ) -> None:
        self._ws_url = ws_url
        self._commitment = commitment
        self._reconnect_delay_sec = reconnect_delay_sec

    async def stream(
        self,
        program_ids: Sequence[str],
        start_slot: int | None = None,
    ) -> AsyncIterator[RawEvent]:
        if not program_ids:
            raise ValueError("At least one program id is required")

        # Import here so the rest of the codebase can be imported without websockets installed.
        import websockets

        while True:
            try:
                async with websockets.connect(self._ws_url, ping_interval=20, ping_timeout=20) as ws:
                    sub_to_program = await self._subscribe(ws, program_ids)

                    logger.info(
                        "WS connected: program_ids=%d start_slot=%s",
                        len(program_ids),
                        start_slot,
                    )

                    async for raw in ws:
                        msg = json.loads(raw)
                        event = self._to_raw_event(msg, sub_to_program)
                        if event is None:
                            continue
                        if start_slot is not None and event.slot < start_slot:
                            continue
                        yield event
            except Exception:
                logger.exception("WS stream error, reconnecting in %.1fs", self._reconnect_delay_sec)
                await asyncio.sleep(self._reconnect_delay_sec)

    async def _subscribe(self, ws: Any, program_ids: Sequence[str]) -> dict[int, str]:
        result: dict[int, str] = {}
        request_id = 1

        for program_id in program_ids:
            req = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "logsSubscribe",
                "params": [
                    {"mentions": [program_id]},
                    {"commitment": self._commitment},
                ],
            }
            await ws.send(json.dumps(req))
            response = json.loads(await ws.recv())
            sub_id = response.get("result")
            if isinstance(sub_id, int):
                result[sub_id] = program_id
                logger.info("Subscribed: program_id=%s subscription=%s", program_id, sub_id)
            else:
                logger.warning("Subscribe failed for program_id=%s response=%s", program_id, response)
            request_id += 1
        return result

    @staticmethod
    def _to_raw_event(message: dict[str, Any], sub_to_program: dict[int, str]) -> RawEvent | None:
        if message.get("method") != "logsNotification":
            return None

        params = message.get("params", {})
        subscription = params.get("subscription")
        result = params.get("result", {})
        value = result.get("value", {})
        context = result.get("context", {})

        signature = value.get("signature")
        slot = context.get("slot")
        if not isinstance(signature, str) or not isinstance(slot, int):
            return None

        program_id = sub_to_program.get(subscription, "unknown")
        return RawEvent(
            signature=signature,
            slot=slot,
            program_id=program_id,
            payload=value,
        )

