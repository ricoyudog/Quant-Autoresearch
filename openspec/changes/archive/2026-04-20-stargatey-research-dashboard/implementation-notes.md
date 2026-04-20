## Group 1: Observer Foundation

### Local dashboard runtime

Chosen stack: Python stdlib `http.server.ThreadingHTTPServer` with a read-only
`BaseHTTPRequestHandler`, vanilla HTML/CSS/JavaScript static assets, and short
browser polling against a JSON endpoint backed by `src.dashboard.observer`.

Rationale:

- No new dependencies are required.
- The existing repo already exposes Typer CLI commands, so a future
  `dashboard` command can launch the stdlib server without changing the
  research-loop execution surface.
- Polling every 2–5 seconds is enough for the first local cockpit because the
  dashboard only reads artifact files and never controls the runner.
- The observer stays independent from the UI so status normalization, stale
  detection, and artifact parsing are unit-testable without starting a server.

Rejected for the first version:

- FastAPI/Flask/Streamlit: faster web scaffolding, but each adds a runtime
  dependency that is not needed for read-only local polling.
- WebSockets or filesystem watchers: useful later, but polling is simpler and
  adequate for the local single-operator dashboard.

### Observer contract

`observe_dashboard_state(repo_root, now=None, stale_after_seconds=600)` reads:

- `experiments/autoresearch_state.json`
- `experiments/iterations/<run_id>/iteration-*/` records, decisions, and logs
- `experiments/results.tsv`

It emits normalized run status, heartbeat diagnostics, iteration summaries,
artifact availability, ledger rows, and source existence metadata for future UI
routes.

### Operator launch and status guide

Launch the read-only dashboard from the repository root:

```bash
uv run python cli.py dashboard
```

Useful options:

- `--repo-root <path>`: point the dashboard at a different repository root.
- `--host 127.0.0.1` and `--port 8765`: change the local bind address.
- `--refresh-seconds 3.0`: adjust browser polling frequency.

The dashboard is read-only and only observes local artifacts; it does not start,
pause, or modify research runs.

#### Run status labels

- `Healthy`: the run is running with a fresh heartbeat and no active iteration claim.
- `Busy`: the state file names an active iteration.
- `Waiting`: no active run state exists yet, or the run has no active iteration and no fresh heartbeat.
- `Stalled`: the latest heartbeat is older than the stale threshold (default 600 seconds).
- `Blocked`: the run state says `blocked`.
- `Failed`: the run state says `failed`.
- `Completed`: the run state says `completed`.

#### Iteration status labels

- `Queued`: the iteration has not produced logs or decision artifacts yet.
- `In Progress`: logs exist and the iteration is still missing final artifacts.
- `Decision Pending`: the iteration is complete enough to evaluate, but no final decision artifact is present yet.
- `Evaluated`: the iteration has a record, but no final keep/revert decision is attached.
- `Kept`: the final decision is keep.
- `Reverted`: the final decision is revert.
- `Follow-up`: the final decision requests a follow-up.
- `Failed`: the iteration or artifact flow failed.

#### Diagnosis messaging

The dashboard prints diagnosis text as `reason`, then detail lines, then any
heartbeat age or missing-artifact markers.

- Run-level diagnosis:
  - `awaiting_state` means the state file is missing.
  - `awaiting_activity` means the state file exists but no active iteration or fresh heartbeat is present.
  - `heartbeat_stale` means the run is stalled; the dashboard also shows the affected iteration, heartbeat age, stale signal, and source path.
  - blocked or failed runs surface `stop_reason`, `last_error`, or the raw status as the reason, plus any split decision details.
  - completed runs surface `stop_reason`, plus `last_completed_iteration=<n>` when available.
- Iteration-level diagnosis:
  - `failed_iteration` surfaces recorded failure reasons or error text.
  - `decision_pending` means the dashboard is waiting on a final decision artifact.
  - `artifacts_pending` means the iteration is still active and missing final artifacts.
  - `queued` means the iteration has not produced logs or decision artifacts yet.
  - `decision_recorded` means the decision reasons are available and are shown directly.

### Group 5 validation evidence

Verification used a representative dashboard fixture rooted at
`experiments/iterations/` with two completed iterations, ledger rows, logs, and
state metadata.

- The representative fixture now derives its timestamps from test execution
  time, so the home-page expectation stays `Healthy` instead of aging into
  `Stalled` during later reruns.
- `uv run pytest tests/integration/test_dashboard_validation.py -q` validates the
  representative artifact tree via the HTTP handler and confirms `/`,
  `/api/state`, and `/iterations/2` respond within 10 seconds.
- `uv run pytest -q` keeps the full repository suite green after the dashboard
  verification harness was added.
- Browser validation used Playwright against a temporary repo root fixture:
  the home page and iteration-detail page both rendered in 2 seconds, the home
  page showed `Healthy` / `run-verify`, and the detail page showed the expected
  hypothesis diff, strategy diff, metric breakdown, and recorded decision
  reasons.

### Group 5 hardening review evidence

Additional pre-archive code review found dashboard hardening gaps around
untrusted browser rendering, repo-relative artifact paths, ambiguous ledger
correlation, stale fallback run selection, and heartbeat freshness.

- Dashboard JavaScript now escapes values before using `innerHTML` for health,
  timeline, recent activity, artifact references, and log excerpts.
- Artifact references resolve repo-relative paths against the observed
  repository root.
- Ledger-backed metrics are only attached when the ledger row has an explicit,
  unambiguous iteration identifier; ambiguous append-only ledger rows remain
  visible in the ledger panel but are not assigned to a specific iteration.
- The observer does not fall back to old run directories when no active state
  file exists.
- Heartbeat selection considers the freshest viable signal across logs,
  artifacts, and state rather than letting any old log dominate liveness.
- Browser smoke validation with malicious log and artifact text rendered the
  strings visibly as text while keeping the dashboard usable.
- The final follow-up removed the last unkeyed single-row ledger fallback and
  resets selected/detail panels when refreshed dashboard state no longer has
  matching iterations.
- Final verification: focused dashboard tests passed, full `uv run pytest -q`
  passed with 355 tests, and Python compile/diff checks passed.
