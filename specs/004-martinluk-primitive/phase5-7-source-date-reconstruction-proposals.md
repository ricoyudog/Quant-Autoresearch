# MartinLuk Phase 5.7 Source Ledger / Public Date Reconstruction Proposals

Generated at: `2026-05-02T10:09:40+00:00`

## Decision

- Overall decision: `proposal_only_no_source_ledger_or_public_date_reconstruction_update`
- T020 state: `- [ ] T020 Launch bounded autoresearch only after validator, focused tests, and replay gates pass`
- Direct source-ledger updates: `0`
- Direct public-date-reconstruction updates: `0`

## No-overclaim boundary

No source-ledger or public-date-reconstruction field is upgraded by this artifact. Existing cited sources remain candidate-window evidence only; exact dates, timestamps, fills, exits, sizes, and account context remain insufficient_evidence until new cited public primary evidence is added.

## Candidate proposals

| Row | Case | Symbol | Cited source IDs | Missing primary fields | Action |
| --- | --- | --- | --- | --- | --- |
| `p5-public-sofi` | `MLUK-SOFI-PULLBACK-PDH-001` | `SOFI` | `lilys_traderlion_2024_transcript` | exact date; entry fill; partial fill; final exit fill; account equity | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |
| `p5-public-amc` | `MLUK-AMC-ORH-REENTRY-002` | `AMC` | `lilys_traderlion_2024_transcript` | exact first attempt timestamp; re-entry timestamp; stop adjustment timestamps; all exits | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |
| `p5-public-coin` | `MLUK-COIN-BTC-INSIDEDAY-003` | `COIN` | `lilys_traderlion_2024_transcript`, `financialwisdom_martin_luk_strategy` | exact BTC context timestamp; entry/exit fills; position size | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |
| `p5-public-lmnd` | `MLUK-LMND-HIGHTIGHTFLAG-004` | `LMND` | `lilys_traderlion_2024_transcript`, `lmnd_sec_q1_2025_shareholder_letter` | exact split-adjusted prices; partial size; volume climax timestamp | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |
| `p5-public-smci` | `MLUK-SMCI-WEEKLYBASE-005` | `SMCI` | `lilys_traderlion_2024_transcript`, `smci_sec_q2_fy2025_preliminary_press_release` | exact date; actual premature exit; would-have-held benchmark | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |

## Public source-near evidence probe added in this pass

- `SOFI` — SoFi IR / SEC filing, “SoFi Reports First Quarter 2026 with Record Net Revenue of $1.1 Billion, Record Member and Product Growth, Net Income of $167 Million” (2026-04-29), https://www.sec.gov/Archives/edgar/data/1818874/000181887426000020/a2026q1earningsrelease.htm. Supported fields: symbol; public catalyst/setup; event/date_window; source citation. Missing fields remain `insufficient_evidence`: exact date; entry fill; partial fill; final exit fill; account equity.
- `AMC` — AMC IR / SEC filing, “AMC Entertainment Holdings, Inc. Reports Fourth Quarter and Full Year 2025 Results” (2026-02-23), https://investor.amctheatres.com/sec-filings/all-sec-filings/content/0001411579-26-000018/amc-20260223xex99d1.htm. Supported fields: symbol; public catalyst/setup; event/date_window; source citation. Missing fields remain `insufficient_evidence`: exact first attempt timestamp; re-entry timestamp; stop adjustment timestamps; all exits.
- `COIN` — Coinbase IR, “Coinbase Delivers on Q4 Financial Outlook, Doubles Total Trading Volume and Crypto Trading Volume Market Share in 2025” (2026-02-12), https://investor.coinbase.com/news/news-details/2026/Coinbase-Delivers-on-Q4-Financial-Outlook-Doubles-Total-Trading-Volume-and-Crypto-Trading-Volume-Market-Share-in-2025/default.aspx. Supported fields: symbol; public catalyst/setup; event/date_window; source citation. Missing fields remain `insufficient_evidence`: exact BTC context timestamp; entry/exit fills; position size.
- `LMND` — SEC EX-99.1, “Shareholder Letter Q1 2025” (2025-05-06), https://www.sec.gov/Archives/edgar/data/1691421/000169142125000062/lmndshareholderletterq12.htm. Supported fields: symbol; public catalyst/setup; event/date_window; source citation. Missing fields remain `insufficient_evidence`: exact split-adjusted prices; partial size; volume climax timestamp.
- `SMCI` — SEC EX-99.1, “Supermicro Announces Second Quarter Fiscal Year 2025 Preliminary Financial Information” (2025-02-11), https://www.sec.gov/Archives/edgar/data/1375365/000137536525000001/q225pressrelease.htm. Supported fields: symbol; public catalyst/setup; event/date_window; source citation. Missing fields remain `insufficient_evidence`: exact date; actual premature exit; would-have-held benchmark.


## Task 2 source-near citation update

These citations are added to the proposal artifact only. They support public symbol/date/catalyst context, but they do **not** close exact operation-level dates, timestamps, fills, trims, exits, size, account equity, realized P&L, or private-account replication. Therefore `source-ledger.json` and `public-date-reconstruction.md` remain unchanged, and every candidate below still preserves `insufficient_evidence` for the listed missing fields.

| Row | Symbol | Added cited source-near evidence | Supported fields | Still insufficient |
| --- | --- | --- | --- | --- |
| `p5-public-sofi` | SOFI | SEC EX-99.1 Q3 2024 earnings release, dated 2024-10-29: `sofi_sec_q3_2024_earnings_release` | public symbol/date/catalyst context inside the reconstructed SOFI window | exact date; entry fill; partial fill; final exit fill; account equity |
| `p5-public-amc` | AMC | SEC/issuer-hosted Form 8-K, period of report 2024-05-13: `amc_sec_2024_05_13_8k` | public symbol/date context around the meme-run window | exact first attempt timestamp; re-entry timestamp; stop adjustment timestamps; all exits |
| `p5-public-coin` | COIN | SEC EX-99.1 Q4/FY2023 shareholder letter, dated 2024-02-15: `coin_sec_q4_2023_shareholder_letter` | public crypto-theme/catalyst context for the reconstructed COIN window | exact BTC context timestamp; entry/exit fills; position size |
| `p5-public-lmnd` | LMND | SEC EX-99.1 Q1 2025 shareholder letter, dated 2025-05-06: `lmnd_sec_q1_2025_shareholder_letter` | public symbol/date/catalyst context only | exact split-adjusted prices; partial size; volume climax timestamp |
| `p5-public-smci` | SMCI | SEC EX-99.1 Q2 FY2025 preliminary financial information, dated 2025-02-11: `smci_sec_q2_fy2025_preliminary_press_release` | public symbol/date/catalyst context only | exact date; actual premature exit; would-have-held benchmark |

## Policy

- Allowed: Add or update source-ledger/public-date-reconstruction only when cited public evidence directly supports a specific missing field.
- Not allowed: Do not infer exact dates/fills/labels from daily bars, diagnostic controls, generic strategy descriptions, or uncited assumptions.
- Current result: No direct canonical source/date updates are made in this task.

## Control gap policy

The 20 Phase 5.6 gap rows are controls; do not add source-ledger/public-date-reconstruction entries for them unless future cited public evidence proves the row itself is a public operation.

## Source artifacts

- `specs/004-martinluk-primitive/phase5-7-missing-primary-evidence-map.json` SHA-256 `8c347e316cf58a1c02d2358784b22b7e16f6217c3eea7ae450d34a27d9351e44`
- `specs/004-martinluk-primitive/phase5-7-public-evidence-upgrade-plan.json` SHA-256 `6e1cfcabdbad288aaf1bcfc2160864e0a76e5ccda231b99e0c22d45c913cf8b8`
- `specs/004-martinluk-primitive/source-ledger.json` SHA-256 `55919c835ba3467f9534206aeb4650752dbd95a5bf04f0bf23118cace824839a`
- `specs/004-martinluk-primitive/public-date-reconstruction.md` SHA-256 `a6c652e9a6963d261287dfdb3f4b78091fcbcf03b5b56ecf70a0525d41f96150`
- `specs/004-martinluk-primitive/public-operation-cases.json` SHA-256 `793017d0e66d96f8de4d429b4a3cf005792dd16f0cf23adecac8c3f96b08c3c3`

## Machine-readable artifact

- `specs/004-martinluk-primitive/phase5-7-source-date-reconstruction-proposals.json` SHA-256 `1079799054d6e7463f6c9de5d63b722c288c18108c5259894ffdf71df9a792b7`
