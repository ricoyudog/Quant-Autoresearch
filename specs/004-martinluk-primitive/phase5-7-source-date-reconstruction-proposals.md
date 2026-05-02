# MartinLuk Phase 5.7 Source Ledger / Public Date Reconstruction Proposals

Generated at: `2026-05-02T03:31:00+00:00`

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
| `p5-public-lmnd` | `MLUK-LMND-HIGHTIGHTFLAG-004` | `LMND` | `lilys_traderlion_2024_transcript` | exact split-adjusted prices; partial size; volume climax timestamp | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |
| `p5-public-smci` | `MLUK-SMCI-WEEKLYBASE-005` | `SMCI` | `lilys_traderlion_2024_transcript` | exact date; actual premature exit; would-have-held benchmark | `no_direct_update_keep_reconstructed_candidate_not_exact_fill` / `no_direct_update_existing_sources_do_not_close_missing_primary_fields` |

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

- `specs/004-martinluk-primitive/phase5-7-source-date-reconstruction-proposals.json`
