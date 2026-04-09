# V2 Minute Autoresearch — Canonical Planning Workspace

## Overview

This workspace is the canonical spec-driven planning surface for the clarified V2 architecture:

- **Karpathy-style autoresearch loop** as the core
- **minute-level strategy discovery/refinement** as the mission
- **TradingAgents-inspired stock-discussion structure** only for strategy-facing research
- **optional factor mining** under the same autoresearch loop
- **backtester-driven keep/revert** as the final success rule

The canonical source of truth for this workspace is:

- `.omx/specs/deep-interview-spec-vs-impl.md`

## Canonical Decisions

| Item | Decision | Why |
| --- | --- | --- |
| Docs root | `docs/` | This repo's live planning root is `docs/` |
| Canonical workspace | `docs/feature/v2-minute-autoresearch/` | This is a feature-scoped V2 architecture effort, not a single bugfix |
| Feature branch | `feature/v2-minute-autoresearch` | Dedicated planning branch based on `main-dev` |
| Merge target | `main-dev` | User explicitly wants the docs package ready for `main-dev` integration |
| Issue topology | one umbrella + four child issues | Smallest issue set that still matches the architecture workstreams |

## GitLab Publication Blocker

**Status:** blocked locally

- `glab` is not installed on this machine
- no GitLab CLI config was found under `~/.config`
- issue cards below are therefore stored as **local publication-ready drafts**
- publish them to GitLab later from a GitLab-capable environment and replace provisional references with real issue IDs/URLs

## Workspace Map

- `v2-minute-autoresearch-development-plan.md` — main phase plan and task tables
- `v2-minute-autoresearch-backend.md` — architecture and runtime lane
- `v2-minute-autoresearch-infra.md` — environment, data, merge-target, and publishing constraints
- `v2-minute-autoresearch-test-plan.md` — verification matrix
- `v2-minute-autoresearch-merge-test-plan.md` — merge-to-`main-dev` verification and publication follow-up
- `issue-cards/` — umbrella + child issue-card drafts
- `sprint1/` — issue A execution docs
- `sprint2/` — issue B execution docs
- `sprint3/` — issue C execution docs
- `sprint4/` — issue D execution docs

## Issue Draft Set

- `issue-cards/umbrella-v2-minute-autoresearch.md`
- `issue-cards/issue-a-autoresearch-core-idea-intake.md`
- `issue-cards/issue-b-minute-runtime-validation.md`
- `issue-cards/issue-c-strategy-stock-discussion.md`
- `issue-cards/issue-d-optional-factor-mining.md`

## Governing Specs

- `.omx/specs/deep-interview-spec-vs-impl.md`
- `docs/research-karpathy-autoresearch.md`
- `docs/research-tradingagents.md`
- `docs/research-capabilities-v2.md`
- `docs/data-pipeline-v2.md`
- `docs/upgrade-plan-v2.md`
- `program.md`

## Acceptance Snapshot

- [ ] GitLab issue drafts are published later with real IDs
- [x] Canonical docs root is explicit
- [x] One canonical feature workspace exists
- [x] Child issue drafts map into `sprintN/` execution docs
- [x] Planning package is written against `main-dev`

