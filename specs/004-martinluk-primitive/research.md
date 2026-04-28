# Research: MartinLuk Primitive Evidence

## Decision

Use Martin Luk's publicly documented process as a new primitive base, but treat it as a public-operation reproducibility target rather than a private-ledger clone.

## Evidence Summary

- USIC/BusinessWire sources confirm competition context and headline returns.
- TraderLion/Castbox summaries describe a 2025 pullback-focused system with anchored VWAP, rising EMAs, 0.5% risk per trade, tight stops, low win rate, and high asymmetry.
- The Lily transcript/summary captures detailed 2024 rules: ADR filters, EMA/dollar-volume/AVWAP indicators, ORH/IRH entries, low-of-day or candle-low stops, trims, and 9/21/50 EMA trailing exits.
- Public social/stream surfaces provide current operation-style clues, but not full fills.

## Rejected Alternatives

1. **Directly mutate `active_strategy.py` from the article summary** — rejected because it would turn an evidence artifact into unvalidated implementation.
2. **Claim exact USIC replication** — rejected because complete fills, account equity, stop modifications, and chart state are not public.
3. **Continue 20-bar momentum filter search** — rejected because the five-hour OMX run showed repeated revert outcomes across similar variants.

## Chosen Primitive

`leader_pullback_orh`:

- leader/hot-theme universe;
- daily/weekly context with EMA and AVWAP support;
- 1m/5m ORH/IRH/prior-high entries;
- hard stop from low-of-day, entry candle low, or setup low;
- 0.5% risk/trade for initial validation;
- partial trims after R expansion;
- 9 EMA close break or strength climax exit.

## Open Questions

- Which public cases can be reconstructed with actual dates and market data?
- Does the local data set include enough daily/minute history for all cited symbols and windows?
- How should AVWAP anchors be represented in the first dry-run version?
- Should short-side GLD/SLV logic remain a separate branch until long-side cases pass?
