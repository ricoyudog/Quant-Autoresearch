# Data Model: MartinLuk Primitive

## SourceLedger

Fields:

- `id`: stable source identifier
- `url`: public source URL
- `type`: source class, e.g. competition result, interview transcript, social mirror
- `use`: how the source informs the primitive
- `confidence`: high, medium_high, medium, medium_low, low

## PublicOperationCase

Fields:

- `case_id`: stable case ID
- `symbol`: ticker or multi-symbol theme
- `direction`: long, short, long_or_short_unknown
- `confidence`: case confidence
- `setup_type`: normalized setup family
- `date_window`: exact date or explicit unknown marker
- `context_rules`: higher-timeframe or market-context requirements
- `entry_trigger`: deterministic trigger to be reproduced
- `stop_rule`: hard stop definition
- `trim_rule`: partial exit rule or insufficient-evidence marker
- `exit_rule`: final exit rule
- `expected_signal_behavior`: what the validator should observe
- `source_ids`: source IDs from `source-ledger.json`
- `missing_fields`: required data not yet public or not yet extracted

## Primitive Parameters

- `risk_per_trade_pct`: default 0.5
- `max_stop_pct`: default 2.5
- `allow_margin`: default false
- `leader_adr_min_pct`: default 5.0
- `avg_dollar_volume_min`: implementation-specific
- `entry_timeframe`: 1m and 5m
- `ema_periods`: 9, 21, 50
- `trail_exit_primary`: 9 EMA close break

## ValidatorResult

Fields:

- `status`: passed, failed, insufficient_evidence
- `passed`: boolean
- `case_count`: integer
- `reproduced_count`: integer
- `unsupported_cases`: list
- `errors`: list
