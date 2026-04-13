#!/usr/bin/env bash

set -euo pipefail

# Claude Code per-iteration wrapper.
#
# This wrapper keeps Claude Code outside the repository runtime while giving the
# outer loop a stable per-iteration invocation contract.

usage() {
  cat <<'EOF' >&2
Usage: scripts/run_claude_iteration.sh <iteration-number> [options] [-- <extra claude args>]

Options:
  --program <path>        Path to program.md (default: program.md)
  --strategy <path>       Path to strategy-under-iteration (default: src/strategies/active_strategy.py)
  --state-file <path>     Path to autoresearch state file (default: experiments/autoresearch_state.json)
  --output-dir <path>     Iteration artifact root (default: experiments/iterations)
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
CLAUDE_BIN="${CLAUDE_CODE_BIN:-claude}"
DRY_RUN=0
EXTRA_ARGS=()
EXTRA_ARGS_COUNT=0

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

if [ ! -f "$PROGRAM_PATH" ]; then
  echo "Program file not found: $PROGRAM_PATH" >&2
  exit 1
fi

if [ ! -f "$STRATEGY_PATH" ]; then
  echo "Strategy file not found: $STRATEGY_PATH" >&2
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
- Do not decide final keep/revert yourself; the outer runner owns acceptance
- Keep edits focused on the strategy-under-iteration unless the outer runner explicitly expands scope
- Leave enough output for the outer runner to summarize the round hypothesis and strategy change
EOF

INVOKE_MODE="${CLAUDE_CODE_INVOKE_MODE:-stdin}"

echo "Claude Code iteration wrapper"
echo "iteration=$ITERATION_NUMBER"
echo "program=$PROGRAM_PATH"
echo "strategy=$STRATEGY_PATH"
echo "state_file=$STATE_FILE"
echo "prompt_file=$PROMPT_PATH"
echo "invoke_mode=$INVOKE_MODE"
echo "claude_bin=$CLAUDE_BIN"

if [ "$DRY_RUN" -eq 1 ]; then
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

case "$INVOKE_MODE" in
  stdin)
    if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
      exec "$CLAUDE_BIN" "${EXTRA_ARGS[@]}" < "$PROMPT_PATH"
    fi
    exec "$CLAUDE_BIN" < "$PROMPT_PATH"
    ;;
  prompt-file)
    if [ "$EXTRA_ARGS_COUNT" -gt 0 ]; then
      exec "$CLAUDE_BIN" "$PROMPT_PATH" "${EXTRA_ARGS[@]}"
    fi
    exec "$CLAUDE_BIN" "$PROMPT_PATH"
    ;;
  *)
    echo "Unsupported CLAUDE_CODE_INVOKE_MODE: $INVOKE_MODE" >&2
    exit 1
    ;;
esac
