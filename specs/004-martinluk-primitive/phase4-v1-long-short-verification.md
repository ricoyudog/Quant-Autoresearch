# Phase 4 Verification: MartinLuk Primitive v1 Long + Short

Date: 2026-04-29
Status: **closed for scenario-gated Phase 4 / Phase 4.1 evidence**

## Scope

This closeout covers the MartinLuk primitive v1 implementation and hardening slice:

- Long-side primitive: leader pullback / opening-range-high breakout.
- Short-side primitive: bounce into declining EMA / AVWAP resistance followed by breakdown.
- Runtime strategy surface:
  - `select_universe(daily_data)` remains mandatory strategy alpha.
  - `generate_signals(minute_data)` keeps returning runtime `pd.Series` / `dict[str, pd.Series]` signals.
  - `get_signal_trace()` exposes validator-compatible side-band trace data.
- Phase 4.1 A hardening tests add scenario coverage for stop-width rejection,
  short reclaim exits, and multi-ticker trace aggregation.

This closeout does **not** start Phase 5.

## Source artifacts

Planning and requirements:

- `.omx/specs/deep-interview-martinluk-primitive-continuation.md`
- `.omx/plans/prd-martinluk-primitive-v1-long-short.md`
- `.omx/plans/test-spec-martinluk-primitive-v1-long-short.md`
- `.omx/plans/ralplan-martinluk-primitive-v1-long-short.md`

Prior validator/risk artifacts:

- `specs/004-martinluk-primitive/public-operation-cases.json`
- `specs/004-martinluk-primitive/public-date-reconstruction.md`
- `specs/004-martinluk-primitive/contracts/public-operation-validator-contract.md`
- `specs/004-martinluk-primitive/phase3-risk-ledger.md`

Implementation and test files:

- `src/strategies/active_strategy.py`
- `tests/unit/test_strategy_interface.py`
- `tests/unit/test_martinluk_public_validator.py`
- `specs/004-martinluk-primitive/validate_public_cases.py`

## Commit evidence

Phase 4 implementation commits already on `main-dev`:

- `074df16` — `Enable scenario-gated long and short primitive execution`
- `4a225e2` — merge of `074df16` into `main-dev`

Phase 4.1 A closeout patch:

- Adds hardening tests in `tests/unit/test_strategy_interface.py`.
- Adds this verification record.
- Final commit hash is represented by the git commit containing this document.

## What Phase 4 proves

Phase 4 proves deterministic **scenario behavior** for the bounded primitive:

1. Long ORH behavior
   - Long entry only after opening-range-high breakout above the EMA.
   - Long hard-stop flattening at the setup low.
   - Long 9-EMA close-break exit.
   - Long support-touch-only rejection without breakout.
   - Long stop-width rejection when risk is too wide.

2. Short declining-EMA / AVWAP behavior
   - Short entry only after declining-resistance bounce and breakdown.
   - Short rejection without failure trigger.
   - Short rejection when high-of-day stop width is too wide.
   - Short hard-stop trace uses direction-aware R math.
   - Short support-cover trace keeps validator diagnostics on direct fields.
   - Short EMA/AVWAP reclaim exit trace remains validator-compatible.

3. Trace contract behavior
   - `generate_signals()` preserves the runtime signal return shape.
   - `get_signal_trace()` carries side-band trace records using schema `martinluk_public_signal_trace_v1`.
   - Multi-ticker dict input aggregates trace entries across tickers.
   - Trace diagnostics stay on direct fields; no nested `diagnostics` object is introduced.

## What Phase 4 does not prove

Phase 4 does **not** prove:

- strategy profitability;
- exact private USIC trade-by-trade replication;
- exact public fill/timestamp reconstruction;
- promotion to Phase 5;
- broad historical backtest validity;
- live/autoresearch production performance.

Public cases with unreconstructable dates/fills remain classified as
`insufficient_evidence`; this is intentional evidence discipline, not a validator
failure.

## Verification evidence

Fresh verification performed for this closeout branch:

```bash
python3 -m py_compile \
  src/strategies/active_strategy.py \
  tests/unit/test_strategy_interface.py \
  specs/004-martinluk-primitive/validate_public_cases.py
```

Result: PASS.

```bash
uv run pytest tests/unit/test_strategy_interface.py -q
```

Result: `36 passed`.

```bash
uv run pytest tests/unit/test_martinluk_public_validator.py -q -p no:cacheprovider
```

Result: `31 passed`.

Synthetic Phase 4.1 trace validator check:

- Trace generated from one long trace scenario and one short EMA/AVWAP reclaim scenario.
- Validator command:

```bash
python3 specs/004-martinluk-primitive/validate_public_cases.py \
  --signals-path /tmp/martinluk-phase41-stop-hook-trace.json
```

Expected result: nonzero exit because public cases remain evidence-limited.

Observed semantic result:

- `errors=[]`
- `classification_counts.data_missing=0`
- `classification_counts.insufficient_evidence=8`
- `classification_counts.not_reproduced=0`
- `classification_counts.reproduced=0`

Repository hygiene:

```bash
git diff --check
```

Result: PASS.

GitNexus change detection:

- Scope: uncommitted/all closeout patch before commit.
- Result: low risk, one changed test file before adding this closeout doc.
- Earlier required impact analysis was run before strategy edits:
  - `TradingStrategy`: HIGH upstream risk because many strategy-interface tests call it directly.
  - `generate_signal_series`: LOW upstream risk with direct caller `generate_signals`.

## Phase 4.1 added hardening tests

The hardening patch adds these scenario tests:

- `test_generate_signals_rejects_long_when_stop_width_exceeds_threshold`
- `test_generate_signals_rejects_short_when_stop_width_exceeds_threshold`
- `test_generate_signals_short_ema_avwap_reclaim_trace_is_validator_compatible`
- `test_generate_signals_keeps_validator_trace_side_band_for_multi_ticker_dict`

These tests deliberately remain synthetic scenario tests. They validate bounded
primitive mechanics and trace-shape discipline only.

## Remaining risks / Phase 5 candidates

Remaining work should be planned separately before execution:

1. Bounded public-case replay planning.
2. Historical validation design with explicit data source and schema boundaries.
3. Treatment of unreconstructable public evidence as `insufficient_evidence`
   unless new primary evidence resolves exact dates/fills.
4. No broad backtest or profit claim without a separate Phase 5 plan and acceptance criteria.

## Closeout decision

Phase 4 / Phase 4.1 is ready to close as a **scenario-gated primitive implementation**.

Next recommended workflow: `$ralplan` for Phase 5 bounded validation design, if
and only if the user approves starting Phase 5.
