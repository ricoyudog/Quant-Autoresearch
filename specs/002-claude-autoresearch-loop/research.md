# Research: Claude Code Autoresearch Loop

## Decision 1: Use Claude Code as an external per-iteration agent, not as embedded repository runtime

**Decision**: The autoresearch system will invoke Claude Code from an outer runner for each round instead of embedding agent orchestration into repository runtime code.

**Rationale**: This matches the Karpathy-style model the user requested: the agent thinks outside the repo, while the repo remains the deterministic evaluator and artifact store.

**Alternatives considered**:

- Build a Python-internal agent loop — rejected because it would pull the repo toward an embedded LLM framework rather than an outer-loop research model.
- Use tmux/team orchestration for every iteration — rejected because the first implementation needs a single bounded runner, not durable multi-worker coordination.

## Decision 2: Keep the evaluator as the final acceptance authority

**Decision**: Keep/revert decisions will be derived from deterministic backtest and validation outputs, not from Claude Code self-assessment.

**Rationale**: The user explicitly wants a Karpathy-like research loop, which still relies on a fixed evaluator. This protects the system from agent optimism and creates an auditable acceptance boundary.

**Alternatives considered**:

- Let Claude Code decide whether a strategy is better — rejected because that would make the loop non-deterministic and harder to trust.
- Use notes-only qualitative approval — rejected because the repository already has a quantitative evaluator and results ledger.

## Decision 3: Persist a single run-state file plus per-iteration artifacts

**Decision**: The loop will persist one run-level state file and one artifact record per iteration.

**Rationale**: A single state file is the simplest reliable resume surface, while per-iteration artifacts preserve auditability without forcing the runner to reconstruct history from logs alone.

**Alternatives considered**:

- Keep all state only in memory — rejected because interruption would destroy progress.
- Write only free-form notes — rejected because resume and automated decisions need structured fields.

## Decision 4: Snapshot and restore the strategy-under-iteration every round

**Decision**: Each round will snapshot the strategy file before Claude Code edits it and will restore that snapshot automatically when the keep rule fails or evaluation errors out.

**Rationale**: This gives the loop a clean, deterministic way to revert failed ideas without depending on Claude Code to clean up after itself.

**Alternatives considered**:

- Ask Claude Code to undo its own changes — rejected because revert behavior should remain outside the agent.
- Use only git commits for every round — rejected because the first implementation needs a simpler reversible unit than a full commit-per-round workflow.

## Decision 5: Stop conditions must be explicit and operator-controlled

**Decision**: The first version will support an iteration budget, a no-improvement limit, and an optional target score.

**Rationale**: Multi-round research must terminate predictably. These three controls are enough to keep early runs bounded without introducing complex search policies.

**Alternatives considered**:

- Run forever — rejected because it is unsafe and difficult to audit.
- Use only one stop condition — rejected because iteration budget alone does not express stagnation, and score target alone does not cap cost.

## Decision 6: Reuse existing repository research surfaces instead of inventing new ones

**Decision**: Each iteration may consume `program.md`, `results.tsv`, recent notes, and the existing `research` / `analyze` commands as context sources.

**Rationale**: The repository already contains the research primitives and memory surfaces needed to inform a round. Reusing them keeps the new runner thin and aligned with current V2 design.

**Alternatives considered**:

- Create a new parallel research context system — rejected because it would duplicate existing vault-native and CLI surfaces.
- Ignore prior notes and only use the current strategy file — rejected because it would make the loop less informed than the current documented workflow.
