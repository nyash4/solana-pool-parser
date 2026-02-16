# New Pool Parser (Solana)

> Demo / Educational Project Notice
>
> This repository is a demonstration of how a modular Solana new-pool parser can be built.
> It is an educational product and may contain limitations, bugs, or incomplete production safeguards.
> Use it as a learning/reference implementation and validate all logic before real trading or production use.

Modular parser for new liquidity pools on Solana.

Current focus:
- Raydium adapter (MVP)
- Easy extension for other aggregators (Orca, Meteora, etc.)

## Architecture

- `pool_parser/core`: shared contracts and pipeline.
- `pool_parser/connectors`: data sources (WebSocket stream + RPC enrichment).
- `pool_parser/adapters`: aggregator-specific detection/parsing logic.
- `pool_parser/storage`: deduplication and state checkpoint.
- `pool_parser/notifier`: delivery of newly detected pools.
- `pool_parser/config`: runtime settings.

## Quick start

1. Create virtualenv and install dependencies:

```bash
pip install -r requirements.txt
```

2. Set env vars (PowerShell):

```powershell
$env:SOLANA_WS_URL="wss://..."
$env:SOLANA_RPC_URL="https://..."
$env:ENABLED_ADAPTERS="raydium"
$env:MAX_TX_AGE_SEC="1800"
```

Use Pump.fun instead:

```powershell
$env:ENABLED_ADAPTERS="pumpfun"
```

Use Jupiter route discovery:

```powershell
$env:ENABLED_ADAPTERS="jupiter"
```

Use Meteora new pools (DLMM + DAMM v2):

```powershell
$env:ENABLED_ADAPTERS="meteora"
```

3. Run:

```bash
python -m pool_parser.app
```

## Add another aggregator

1. Create new adapter in `pool_parser/adapters/<name>/adapter.py`.
2. Implement `PoolAdapter` protocol from `pool_parser/core/interfaces.py`.
3. Register adapter in `pool_parser/adapters/registry.py`.
4. Enable it via `ENABLED_ADAPTERS=raydium,orca` (example).

## Adapter notes

- `pumpfun`: parses Pump and PumpSwap create events.
- `jupiter`: parses Jupiter-routed transactions and extracts pools from supported underlying AMM instructions.
- `meteora`: parses Meteora DLMM and DAMM v2 pool initialization instructions.

`MAX_TX_AGE_SEC` controls freshness filter for parsed transactions.

The pipeline and storage remain unchanged.

## Notes about Raydium decoder

Current Raydium parsing is intentionally conservative and partly heuristic:
- pool creation detection is based on log patterns.
- token and pool extraction is best-effort from parsed transaction data.

For production-grade parsing, refine `decoder.py` with exact instruction layouts per Raydium program version.
