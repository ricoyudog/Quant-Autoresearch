# System Architecture: Legacy Note

This file is retained as a short historical placeholder. It does not describe
the active runtime architecture of Quant Autoresearch.

## Current V2 References

Use these files for the current architecture instead:

- `README.md`
- `CLAUDE.md`
- `program.md`
- `src/core/backtester.py`
- `src/data/connector.py`
- `src/strategies/active_strategy.py`

## Current Runtime Summary

The active V2 workflow is:

1. follow `program.md` as the experiment contract
2. edit `src/strategies/active_strategy.py`
3. run validation through `cli.py` or `src/core/backtester.py`
4. use cached data from `data/cache/`
5. record experiment outputs in local result logs and notes

Optional helpers such as `src/core/research.py` and `src/memory/playbook.py`
still exist, but they are supporting modules rather than the primary runtime
loop.

## Historical Context

Earlier versions of this repository used a Python-side orchestration stack that
is no longer the active design. Those removed components should not be treated
as current architecture guidance.
