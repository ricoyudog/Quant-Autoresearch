#!/usr/bin/env bash

set -euo pipefail

# Claude Code per-iteration wrapper.
#
# This wrapper keeps Claude Code outside the repository runtime while giving the
# outer loop a stable per-iteration invocation contract.

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<'EOF' >&2
Usage: scripts/run_claude_iteration.sh <iteration-number> [options] [-- <extra claude args>]

Options:
  --program <path>        Path to program.md (default: program.md)
  --strategy <path>       Path to strategy-under-iteration (default: src/strategies/active_strategy.py)
  --state-file <path>     Path to autoresearch state file (default: experiments/autoresearch_state.json)
  --output-dir <path>     Iteration artifact root (default: experiments/iterations)
  --context-file <path>   Optional markdown context bundle for the round prompt
  --claude-bin <path>     Claude Code executable (default: $CLAUDE_CODE_BIN or claude)
  --dry-run               Build prompt artifact and print the planned invocation without executing Claude Code
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
CLAUDE_BIN="${CLAUDE_CODE_BIN:-claude}"
CLAUDE_DEFAULT_ARGS=("--dangerously-skip-permissions")
CLAUDE_RATE_LIMIT_EXIT_CODE=75
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
    --claude-bin)
      CLAUDE_BIN="$2"
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
mkdir -p "$ROUND_DIR"

cat > "$PROMPT_PATH" <<EOF
# Claude Code Iteration Prompt

Iteration: $ITERATION_NUMBER
Program: $PROGRAM_PATH
Strategy Target: $STRATEGY_PATH
State File: $STATE_FILE

You are running one bounded autoresearch iteration for Quant Autoresearch.

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
- Leave enough output for the outer runner to summarize the round hypothesis, proofable idea sources, stock/ETF universe selection thesis, and strategy change
- Final response must be a JSON object with keys: hypothesis, strategy_change_summary, universe_selection_summary, proofable_idea_sources, files_touched
EOF

if [ -n "$CONTEXT_FILE" ]; then
  {
    printf '\nContext Bundle:\n\n'
    cat "$CONTEXT_FILE"
  } >> "$PROMPT_PATH"
fi

INVOKE_MODE="${CLAUDE_CODE_INVOKE_MODE:-stdin}"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "Claude Code iteration wrapper"
  echo "iteration=$ITERATION_NUMBER"
  echo "program=$PROGRAM_PATH"
  echo "strategy=$STRATEGY_PATH"
  echo "state_file=$STATE_FILE"
  echo "context_file=$CONTEXT_FILE"
  echo "prompt_file=$PROMPT_PATH"
  echo "invoke_mode=$INVOKE_MODE"
  echo "claude_bin=$CLAUDE_BIN"
  echo "status=dry_run"
  if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
    EXTRA_ARGS_JOINED="${EXTRA_ARGS[*]}"
    printf 'extra_args=%s\n' "$EXTRA_ARGS_JOINED"
  fi
  exit 0
fi

if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
  echo "Claude Code executable not found: $CLAUDE_BIN" >&2
  exit 1
fi

emit_runtime_banner() {
  {
    echo "Claude Code iteration wrapper"
    echo "iteration=$ITERATION_NUMBER"
    echo "program=$PROGRAM_PATH"
    echo "strategy=$STRATEGY_PATH"
    echo "state_file=$STATE_FILE"
    echo "context_file=$CONTEXT_FILE"
    echo "prompt_file=$PROMPT_PATH"
    echo "invoke_mode=$INVOKE_MODE"
    echo "claude_bin=$CLAUDE_BIN"
  } >&2
}

run_claude_with_contract() {
  local stdout_file stderr_file exit_code combined_output
  stdout_file=$(mktemp)
  stderr_file=$(mktemp)
  emit_runtime_banner

  if [ "$INVOKE_MODE" = "stdin" ]; then
    if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
      IS_SANDBOX=1 "$CLAUDE_BIN" "${CLAUDE_DEFAULT_ARGS[@]}" "${EXTRA_ARGS[@]}" < "$PROMPT_PATH" >"$stdout_file" 2>"$stderr_file" || exit_code=$?
    else
      IS_SANDBOX=1 "$CLAUDE_BIN" "${CLAUDE_DEFAULT_ARGS[@]}" < "$PROMPT_PATH" >"$stdout_file" 2>"$stderr_file" || exit_code=$?
    fi
  else
    if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
      IS_SANDBOX=1 "$CLAUDE_BIN" "${CLAUDE_DEFAULT_ARGS[@]}" "$PROMPT_PATH" "${EXTRA_ARGS[@]}" >"$stdout_file" 2>"$stderr_file" || exit_code=$?
    else
      IS_SANDBOX=1 "$CLAUDE_BIN" "${CLAUDE_DEFAULT_ARGS[@]}" "$PROMPT_PATH" >"$stdout_file" 2>"$stderr_file" || exit_code=$?
    fi
  fi

  exit_code=${exit_code:-0}
  cat "$stdout_file"
  cat "$stderr_file" >&2
  combined_output="$(cat "$stdout_file" "$stderr_file")"
  rm -f "$stdout_file" "$stderr_file"

  if [ "$exit_code" -ne 0 ] && printf '%s' "$combined_output" | grep -Eq 'API Error: 429|Rate limit reached for requests|"code":"1302"|"code": "1302"'; then
    exit "$CLAUDE_RATE_LIMIT_EXIT_CODE"
  fi

  exit "$exit_code"
}

case "$INVOKE_MODE" in
  stdin)
    run_claude_with_contract
    ;;
  prompt-file)
    run_claude_with_contract
    ;;
  *)
    echo "Unsupported CLAUDE_CODE_INVOKE_MODE: $INVOKE_MODE" >&2
    exit 1
    ;;
esac
