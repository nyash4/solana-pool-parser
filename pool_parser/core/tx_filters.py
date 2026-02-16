from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def is_tx_fresh(tx_result: dict[str, Any], max_age_sec: int | None) -> bool:
    if max_age_sec is None or max_age_sec <= 0:
        return True

    block_time = tx_result.get("blockTime")
    if not isinstance(block_time, int):
        # Do not drop if provider did not return blockTime.
        return True

    now_ts = int(datetime.now(timezone.utc).timestamp())
    age = now_ts - block_time
    if age < 0:
        # Clock skew or near-future timestamp from RPC response.
        return True
    return age <= max_age_sec

