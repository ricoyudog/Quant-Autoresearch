# Public Date Reconstruction: MartinLuk Primitive Cases

Generated: 2026-04-28T04:58:00Z

Scope: reconstruct expected signal windows for the five long-side public examples in
`public-operation-cases.json`: SOFI, AMC, COIN, LMND, and SMCI.

Boundary: these are **candidate public signal windows**, not private ledger fills.
The public interview page uses chart pointers instead of machine-readable execution
records, so exact entry, trim, exit, size, and account-equity fields remain
unsupported unless a future source exposes them.

Public source IDs reused from `source-ledger.json`:

- `lilys_traderlion_2024_transcript` — https://lilys.ai/ko/notes/887808
- `financialwisdom_martin_luk_strategy` — https://www.financialwisdomtv.com/post/martin-luk-s-1358-swing-trading-strategy-from-gamestop-blow-up-to-us-investing-champion

Daily bar cross-check: Yahoo Finance daily history accessed through the existing
project `yfinance` dependency with `uv run python` on 2026-04-28. This did not add
or change dependencies. Market data was used only to align public narrative clues
with plausible calendar windows.

## Reconstruction table

| Case | Status | Expected public signal window | Public evidence | Daily-bar alignment | Still unsupported |
| --- | --- | --- | --- | --- | --- |
| `MLUK-SOFI-PULLBACK-PDH-001` | candidate, medium confidence | setup/pullback 2024-10-29..2024-11-04; trigger candidate 2024-11-05; management/exit check 2024-12-18..2024-12-19 | `lilys_traderlion_2024_transcript` idx 459-467 describes SOFI moving from about 7 to 11/12, a three-day pullback near the 9 EMA, prior-day-high entry, day-low stop, 6R trim, and exit below the 9 EMA into December. | SOFI daily bars show the October run into the 11/12 area, a pullback near the local 9 EMA around 2024-10-29..2024-11-04, a 2024-11-05 prior-high break, and weak closes below the local 9 EMA on 2024-12-18/19. | exact fill dates/prices, partial-fill size, final exit fill, account equity |
| `MLUK-AMC-ORH-REENTRY-002` | candidate, medium-high confidence | 2024-05-13..2024-05-14 | `lilys_traderlion_2024_transcript` idx 443-458 describes AMC after the GME May example, a first 5m ORH stopout, inside-day/range re-entry, about 3.22% stop, about 170% move from entry, 100% premarket strength, and trim around the 9.50/10 resistance area. | AMC daily bars isolate the two-day meme run on 2024-05-13 and 2024-05-14; the 2024-05-14 high reached the 9.50/10 area and above on extreme volume. | exact 5m candles, first-attempt timestamp, re-entry timestamp, stop-adjustment timestamps, all exits |
| `MLUK-COIN-BTC-INSIDEDAY-003` | candidate, medium confidence | 2024-02-07..2024-02-16 | `lilys_traderlion_2024_transcript` idx 360-366 describes COIN bought near a low-of-day reclaim while Bitcoin formed an inside-day/prior-high breakout context. `financialwisdom_martin_luk_strategy` corroborates a COIN example with entry around 117, 2% stop, and roughly 20R/40% gain; used only as corroboration. | COIN daily bars show a plausible 117-area low-of-day reclaim on 2024-02-07 followed by a move into the 140/160 area through 2024-02-14..2024-02-16. This fits the public 117-entry clue better than the later 2024-02-26 BTC breakout. | exact BTC trigger timestamp, exact COIN fills, position size, panic-sale/second-trade separation |
| `MLUK-LMND-HIGHTIGHTFLAG-004` | candidate, medium-high confidence | setup 2024-11-15..2024-11-18; trigger candidate 2024-11-19; strength/volume exit check 2024-11-20..2024-11-21 | `lilys_traderlion_2024_transcript` idx 514-530 describes Lemonade as a quick high-tight-flag trade with repeated inside days, prior-day-high breakout, 2.5%-3% stop, 8R partial, and volume-driven strength exit. | LMND daily bars show a tight/inside-day setup around 2024-11-18, breakout above the prior day high on 2024-11-19, and acceleration on high volume on 2024-11-20/21. | exact split-adjusted entry/partial prices, partial size, intraday volume-climax timestamp |
| `MLUK-SMCI-WEEKLYBASE-005` | candidate, medium-high confidence | 2024-01-16..2024-01-19 | `lilys_traderlion_2024_transcript` idx 312-336 describes SMCI as a 2024 public example, on watch since December 2023, with a six-month weekly base from August, tight January 2024 candles after failed December breakout attempts, nonoptimal entry, and preferred prior-day-high breakout. | SMCI daily bars show tight January setup days on 2024-01-16..2024-01-18 and high-volume range expansion on 2024-01-19. | exact entry date, actual premature exit date, would-have-held benchmark, fills |

## Unsupported-case rule

A validator or downstream strategy trace must not treat these candidate windows as
complete private ledger data. If a signal trace requires exact timestamps, fills,
position sizing, or broker-execution details, the correct status remains
`insufficient_evidence` rather than a silent pass.
