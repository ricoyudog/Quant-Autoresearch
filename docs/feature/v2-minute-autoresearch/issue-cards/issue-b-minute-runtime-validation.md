# Issue Draft B — Minute Runtime + Validation Alignment

**Publication Status**

- Published on GitHub as [#19](https://github.com/ricoyudog/Quant-Autoresearch/issues/19)
- Applied label: `workflow::done`
- Merged to `main-dev` via [PR #24](https://github.com/ricoyudog/Quant-Autoresearch/pull/24) on `2026-04-09`

**Feature Branch**

- `feature/v2-minute-autoresearch`

**Goal**

- Converge the runtime architecture on the clarified minute-level mission while preserving the backtester as a hard invariant.

**Scope**

- minute-level mission enforcement
- data/runtime alignment
- backtester invariants
- keep/revert authority

**Out of Scope**

- stock discussion UX or discussion structure
- factor-mining mode details

**Docs Workspace**

- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-infra.md`

**Governing Specs**

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/data-pipeline-v2.md`
- `docs/feature/v2-data-pipeline/v2-data-pipeline-development-plan.md`

**Phase Plan**

| Phase | Goal | Deliverables | Status | Next Step |
| --- | --- | --- | --- | --- |
| Sprint 2 | define minute runtime and validation alignment | sprint2 backend/infra docs plus merged backtester/runtime guard | completed | none |

**Task Table**

| Task ID | Task | Owner | Dependency | Effort | Acceptance |
| --- | --- | --- | --- | --- | --- |
| B-01 | Define minute-level runtime contract | BE | none | 0.2d | minute mission is explicit in runtime docs |
| B-02 | Define backtester invariants and keep/revert gate | BE | B-01 | 0.2d | validation engine remains non-negotiable |
| B-03 | Define environment/data prerequisites for minute pipeline | Infra | B-01 | 0.2d | prerequisites and merge assumptions are explicit |

**Detailed Todo**

- [x] define minute-level mission enforcement
- [x] define how current runtime drifts from target runtime
- [x] define invariant-preserving implementation constraints

**Dependencies / Risks**

- current branch/runtime drift
- minute-pipeline complexity could push design away from autoresearch simplicity

**Verification Plan**

- sprint2 docs exist and link back to canonical spec

**Verification Evidence**

- `uv run pytest tests/unit/test_backtester_v2.py tests/unit/test_cli.py tests/unit/test_duckdb_connector.py tests/integration/test_minute_backtest.py -q` → `87 passed`
- `uv run python -m compileall src config cli.py` → completed without compile errors

**Implementation Summary**

- Removed the public V2 fallback from `walk_forward_validation()` when daily DuckDB inputs are missing
- Enforced a stable `DATA ERROR` for missing minute-runtime prerequisites
- Synchronized Sprint 2 backend/infra docs to the enforced minute-runtime-only contract

**Closeout Notes**

- Remaining legacy helper functions in `src/core/backtester.py` are compatibility scaffolding only; the public V2 path now fails explicitly instead of silently dropping into the legacy runtime.

**Acceptance Criteria**

- [x] sprint2 docs are execution-ready
- [x] backtester invariants are treated as hard requirements

**References**

- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-backend.md`
- `docs/feature/v2-minute-autoresearch/sprint2/sprint2-infra.md`
- `src/core/backtester.py`
- `tests/unit/test_backtester_v2.py`
- [PR #24](https://github.com/ricoyudog/Quant-Autoresearch/pull/24)
- [Issue #19](https://github.com/ricoyudog/Quant-Autoresearch/issues/19)
