#!/usr/bin/env bash

set -euo pipefail

# OMX/Codex per-iteration wrapper.
#
# This wrapper matches the existing autoresearch runner wrapper contract while
# routing the strategy-improvement step through `omx exec`.

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<'EOF' >&2
Usage: scripts/run_omx_iteration.sh <iteration-number> [options] [-- <extra omx exec args>]

Options:
  --program <path>        Path to program.md (default: program.md)
  --strategy <path>       Path to strategy-under-iteration (default: src/strategies/active_strategy.py)
  --state-file <path>     Path to autoresearch state file (default: experiments/autoresearch_state.json)
  --output-dir <path>     Iteration artifact root (default: experiments/iterations)
  --context-file <path>   Optional markdown context bundle for the round prompt
  --omx-bin <path>        OMX executable (default: $OMX_BIN or omx)
  --dry-run               Build prompt artifact and print the planned invocation without executing OMX
  --help                  Show this message
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

ITERATION_NUMBER="$1"
shift || true

if ! [[ "$ITERATION_NUMBER" =~ ^[0-9]+$ ]]; then
  echo "Iteration number must be an integer." >&2
  exit 1
fi

PROGRAM_PATH="program.md"
STRATEGY_PATH="src/strategies/active_strategy.py"
STATE_FILE="experiments/autoresearch_state.json"
OUTPUT_DIR="experiments/iterations"
CONTEXT_FILE=""
OMX_BIN="${OMX_BIN:-omx}"
DRY_RUN=0
EXTRA_ARGS=()
EXTRA_ARGS_COUNT=0

resolve_repo_path() {
  local input_path="$1"
  if [ -z "$input_path" ]; then
    printf '%s\n' "$input_path"
    return
  fi
  case "$input_path" in
    /*) printf '%s\n' "$input_path" ;;
    *) printf '%s\n' "$REPO_ROOT/$input_path" ;;
  esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --program)
      PROGRAM_PATH="$2"
      shift 2
      ;;
    --strategy)
      STRATEGY_PATH="$2"
      shift 2
      ;;
    --state-file)
      STATE_FILE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --context-file)
      CONTEXT_FILE="$2"
      shift 2
      ;;
    --omx-bin)
      OMX_BIN="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ARGS+=("$@")
      EXTRA_ARGS_COUNT=$#
      break
      ;;
    *)
      EXTRA_ARGS+=("$1")
      EXTRA_ARGS_COUNT=$((EXTRA_ARGS_COUNT + 1))
      shift
      ;;
  esac
done

PROGRAM_PATH="$(resolve_repo_path "$PROGRAM_PATH")"
STRATEGY_PATH="$(resolve_repo_path "$STRATEGY_PATH")"
STATE_FILE="$(resolve_repo_path "$STATE_FILE")"
OUTPUT_DIR="$(resolve_repo_path "$OUTPUT_DIR")"
if [ -n "$CONTEXT_FILE" ]; then
  CONTEXT_FILE="$(resolve_repo_path "$CONTEXT_FILE")"
fi

if [ ! -f "$PROGRAM_PATH" ]; then
  echo "Program file not found: $PROGRAM_PATH" >&2
  exit 1
fi

if [ ! -f "$STRATEGY_PATH" ]; then
  echo "Strategy file not found: $STRATEGY_PATH" >&2
  exit 1
fi

if [ -n "$CONTEXT_FILE" ] && [ ! -f "$CONTEXT_FILE" ]; then
  echo "Context file not found: $CONTEXT_FILE" >&2
  exit 1
fi

ITERATION_LABEL=$(printf "%04d" "$ITERATION_NUMBER")
ROUND_DIR="$OUTPUT_DIR/iteration-$ITERATION_LABEL"
PROMPT_PATH="$ROUND_DIR/claude_prompt.md"
SUMMARY_PATH="$ROUND_DIR/omx_summary.json"
OMX_STDOUT_PATH="$ROUND_DIR/omx_exec.stdout.log"
OMX_STDERR_PATH="$ROUND_DIR/omx_exec.stderr.log"
SUMMARY_WAIT_SECONDS="${OMX_SUMMARY_WAIT_SECONDS:-300}"
mkdir -p "$ROUND_DIR"

cat > "$PROMPT_PATH" <<EOF
# OMX Codex Iteration Prompt

Iteration: $ITERATION_NUMBER
Program: $PROGRAM_PATH
Strategy Target: $STRATEGY_PATH
State File: $STATE_FILE

You are running one bounded autoresearch iteration for Quant Autoresearch through OMX/Codex.

Required behavior:
- Read the repository program from \`$PROGRAM_PATH\`
- Read the current strategy from \`$STRATEGY_PATH\`
- Read prior run state from \`$STATE_FILE\` when available
- Propose and implement one bounded strategy improvement only
- Any strategy you leave behind must implement both \`select_universe(daily_data)\` and \`generate_signals(minute_data)\`
- Treat universe selection and minute-level signal generation as one connected strategy surface
- Do not decide final keep/revert yourself; the outer runner owns acceptance
- Do not bypass evaluator-led governance with fallback universes, self-approved keeps, or new governance states
- Keep edits focused on the strategy-under-iteration unless the outer runner explicitly expands scope
- Do not edit tests, docs, runner code, metadata, or generated artifacts; run existing checks only
- Leave enough output for the outer runner to summarize the round hypothesis, proofable idea sources, stock/ETF universe selection thesis, and strategy change
- Final response must be a JSON object with keys: hypothesis, strategy_change_summary, universe_selection_summary, proofable_idea_sources, files_touched
EOF

if [ -n "$CONTEXT_FILE" ]; then
  {
    printf '\nContext Bundle:\n\n'
    cat "$CONTEXT_FILE"
  } >> "$PROMPT_PATH"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "OMX Codex iteration wrapper"
  echo "iteration=$ITERATION_NUMBER"
  echo "program=$PROGRAM_PATH"
  echo "strategy=$STRATEGY_PATH"
  echo "state_file=$STATE_FILE"
  echo "context_file=$CONTEXT_FILE"
  echo "prompt_file=$PROMPT_PATH"
  echo "summary_file=$SUMMARY_PATH"
  echo "omx_bin=$OMX_BIN"
  echo "status=dry_run"
  if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
    EXTRA_ARGS_JOINED="${EXTRA_ARGS[*]}"
    printf 'extra_args=%s\n' "$EXTRA_ARGS_JOINED"
  fi
  exit 0
fi

if ! command -v "$OMX_BIN" >/dev/null 2>&1; then
  echo "OMX executable not found: $OMX_BIN" >&2
  exit 1
fi

emit_runtime_banner() {
  {
    echo "OMX Codex iteration wrapper"
    echo "iteration=$ITERATION_NUMBER"
    echo "program=$PROGRAM_PATH"
    echo "strategy=$STRATEGY_PATH"
    echo "state_file=$STATE_FILE"
    echo "context_file=$CONTEXT_FILE"
    echo "prompt_file=$PROMPT_PATH"
    echo "summary_file=$SUMMARY_PATH"
    echo "omx_stdout=$OMX_STDOUT_PATH"
    echo "omx_stderr=$OMX_STDERR_PATH"
    echo "omx_bin=$OMX_BIN"
  } >&2
}

emit_runtime_banner
set +e
if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
  IS_SANDBOX=1 "$OMX_BIN" exec \
    --dangerously-bypass-approvals-and-sandbox \
    -C "$REPO_ROOT" \
    -o "$SUMMARY_PATH" \
    "${EXTRA_ARGS[@]}" \
    < "$PROMPT_PATH" >"$OMX_STDOUT_PATH" 2>"$OMX_STDERR_PATH" &
else
  IS_SANDBOX=1 "$OMX_BIN" exec \
    --dangerously-bypass-approvals-and-sandbox \
    -C "$REPO_ROOT" \
    -o "$SUMMARY_PATH" \
    < "$PROMPT_PATH" >"$OMX_STDOUT_PATH" 2>"$OMX_STDERR_PATH" &
fi
OMX_CHILD_PID=$!

summary_is_valid() {
  python3 - "$SUMMARY_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if not isinstance(payload, dict):
    raise SystemExit(1)
if not isinstance(payload.get("hypothesis"), str) or not payload["hypothesis"].strip():
    raise SystemExit(1)
if not isinstance(payload.get("strategy_change_summary"), str) or not payload["strategy_change_summary"].strip():
    raise SystemExit(1)
if not isinstance(payload.get("universe_selection_summary"), str) or not payload["universe_selection_summary"].strip():
    raise SystemExit(1)
proofable_sources = payload.get("proofable_idea_sources")
if not isinstance(proofable_sources, list) or not all(isinstance(item, (str, dict)) for item in proofable_sources):
    raise SystemExit(1)
files_touched = payload.get("files_touched")
if not isinstance(files_touched, list) or not all(isinstance(item, str) for item in files_touched):
    raise SystemExit(1)
PY
}

EXIT_CODE=""
for _ in $(seq 1 "$SUMMARY_WAIT_SECONDS"); do
  if [ -s "$SUMMARY_PATH" ] && summary_is_valid; then
    EXIT_CODE=0
    break
  fi
  if ! kill -0 "$OMX_CHILD_PID" 2>/dev/null; then
    wait "$OMX_CHILD_PID"
    EXIT_CODE=$?
    break
  fi
  sleep 1
done

if [ -z "$EXIT_CODE" ]; then
  EXIT_CODE=124
fi

if kill -0 "$OMX_CHILD_PID" 2>/dev/null; then
  kill -TERM "$OMX_CHILD_PID" 2>/dev/null || true
  sleep 1
  if kill -0 "$OMX_CHILD_PID" 2>/dev/null; then
    kill -KILL "$OMX_CHILD_PID" 2>/dev/null || true
  fi
  wait "$OMX_CHILD_PID" 2>/dev/null || true
fi
set -e

if [ "$EXIT_CODE" -ne 0 ]; then
  cat "$OMX_STDOUT_PATH" >&2 || true
  cat "$OMX_STDERR_PATH" >&2 || true
  exit "$EXIT_CODE"
fi

if [ ! -s "$SUMMARY_PATH" ]; then
  echo "Missing OMX summary: $SUMMARY_PATH" >&2
  exit 1
fi

if ! summary_is_valid; then
  echo "Invalid OMX summary: $SUMMARY_PATH" >&2
  exit 1
fi

cat "$SUMMARY_PATH"
printf '\n'
