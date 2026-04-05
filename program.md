# Quant Autoresearch

Autonomous quantitative strategy discovery.

## Setup

To set up a new experiment:
1. **Agree on a run tag** with the user (e.g. `apr1`).
   The branch `quant-research/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b quant-research/<tag>` from main.
3. **Read the in-scope files**:
   - `src/core/backtester.py` — fixed evaluation harness. Do NOT modify.
   - `src/strategies/active_strategy.py` — the file you modify.
4. **Verify data exists**: Check `data/cache/` has Parquet files.
   If not, tell the human to run `uv run python cli.py setup_data`.
5. **Initialize files**:
   - Create `experiments/results.tsv` with header row if needed.
   - Create `experiments/notes/` directory.
6. **Run baseline** — always run the unmodified strategy first.
7. **Confirm and go**.

## Experimentation

Each experiment:
```bash
uv run python src/core/backtester.py > experiments/run.log 2>&1
```

**What you CAN do:**
- Modify `src/strategies/active_strategy.py` — the ENTIRE file is fair game.
  Change class names, add methods, change hyperparameters, redesign signal logic.
  The only requirement: the file must define at least one class with a
  `generate_signals(self, data)` method that returns a Series of signals.

**What you CANNOT do:**
- Modify `src/core/backtester.py`. It is read-only.
- Install new packages. The sandbox only provides `pd` and `np`.
- Use `for` loops. Vectorized Pandas/NumPy only.
- Use `.shift(-N)` (look-ahead bias).

## The goal

Get the highest **SCORE** (Average Walk-Forward OOS Sharpe Ratio).

## Output format

```
---
SCORE: 0.4521
NAIVE_SHARPE: 0.6832
NW_SHARPE_BIAS: 0.2311
DEFLATED_SR: 0.9200
SORTINO: 0.8100
CALMAR: 1.2300
DRAWDOWN: -0.1200
MAX_DD_DAYS: 45
TRADES: 120
WIN_RATE: 0.5500
PROFIT_FACTOR: 1.8500
AVG_WIN: 0.0120
AVG_LOSS: -0.0080
BASELINE_SHARPE: 0.4500
---
PER_SYMBOL:
  SPY: sharpe=0.62 sortino=0.90 dd=-0.10 pf=2.10 trades=35 wr=0.57
  ...
```

Extract:
```bash
grep "^SCORE:\|^NAIVE_SHARPE:\|^NW_SHARPE_BIAS:\|^DEFLATED_SR:\|^BASELINE_SHARPE:" experiments/run.log
```

## Decision rules

**KEEP if:**
- SCORE > previous best AND
- SCORE > BASELINE_SHARPE

**DISCARD if:**
- SCORE <= previous best OR
- SCORE <= BASELINE_SHARPE (can't beat Buy&Hold)

**Advisories:**
- If `DEFLATED_SR < 0.5`, treat the result as not robust yet and run deeper validation before trusting it.
- If `NW_SHARPE_BIAS > 0.3`, serial correlation is materially inflating the naive estimate.

## Overfit Defense Guidance

- `SCORE` is now the Newey-West adjusted Sharpe Ratio, not the naive Sharpe.
- `NAIVE_SHARPE` is retained only as a comparison point.
- `NW_SHARPE_BIAS = NAIVE_SHARPE - SCORE`; larger values indicate more serial-correlation inflation.
- Use advanced validation when a change improves `SCORE` by more than `0.05`, after parameter changes, and at least every `5-10` experiments.
- Red flags:
  - `NW_SHARPE_BIAS > 0.3`
  - `DEFLATED_SR < 0.5`
  - future CPCV percent-positive below `50%`
  - future stability score below `0.5`

**Simplicity criterion**:
All else being equal, simpler is better.
- Removing code and getting equal or better results -> great outcome.
- A 0.01 Sharpe improvement that adds 20 lines of hacky complexity -> probably not worth it.
- A 0.01 Sharpe improvement from deleting code -> definitely keep.

## Logging results

Log to `experiments/results.tsv` (tab-separated, do NOT commit):
```
commit  score  naive_sharpe  deflated_sr  sortino  calmar  drawdown  max_dd_days  trades  win_rate  profit_factor  avg_win  avg_loss  baseline_sharpe  nw_bias  status  description
```

## Obsidian experiment notes

After each experiment, write a note to `experiments/notes/<NNN>-<slug>.md`.

### Note format

Each note MUST follow this structure:

````markdown
---
id: 003
commit: f6g7h8i
date: 2026-04-01T14:30:00
status: keep
tags: [momentum, regime-filter, combination]
---

# Experiment 003: Combine momentum + regime filter

## Hypothesis
Combining the ROC momentum signal with the ATR regime filter should reduce
false signals during high-volatility periods while maintaining trend capture.

## Changes
- Modified signal logic in `generate_signals()`:
  - Added ROC(14) as primary momentum indicator
  - Used ATR EMA regime filter as gate
  - Only go long/short when regime is low-vol AND momentum confirms

## Results
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Sharpe | 0.6500 | +0.1068 |
| Sortino | 0.9800 | +0.1700 |
| Profit Factor | 2.3000 | +0.4500 |
| Win Rate | 60% | +5% |
| Deflated SR | 0.92 | Robust after multiple-testing penalty |
| NW Bias | 0.12 | Mild serial-correlation inflation |

## Per-Symbol
- SPY: 0.62 (strong in low-vol regime)
- QQQ: 0.58 (good trend capture)
- IWM: 0.43 (weaker, needs investigation)
- BTC: 0.54 (decent, crypto regime detection works)

## Observations
- IWM underperforms — likely because small-cap regime behavior differs
- Consider symbol-specific regime thresholds in next experiment
- Profit Factor improvement suggests the filter is cutting bad trades effectively

## Next Ideas
- [ ] Try symbol-specific ATR thresholds
- [ ] Add a momentum acceleration indicator
- [ ] Test with longer lookback (20 → 30)
````

## The experiment loop

LOOP FOREVER:
1. Check git state: current branch/commit
2. Read `experiments/results.tsv` for history
3. Propose hypothesis -> modify `src/strategies/active_strategy.py`
4. `git add src/strategies/active_strategy.py && git commit -m "<description>"`
5. `uv run python src/core/backtester.py > experiments/run.log 2>&1`
6. `grep "^SCORE:\|^DEFLATED_SR:\|^NW_SHARPE_BIAS:\|^BASELINE_SHARPE:" experiments/run.log`
7. If grep empty -> crash. `tail -n 50 experiments/run.log`. Fix or skip.
8. Check hard constraints (`SCORE`, `BASELINE_SHARPE`) and advisories (`DEFLATED_SR`, `NW_SHARPE_BIAS`)
9. Record in `experiments/results.tsv`
10. Write Obsidian note
11. If KEEP -> keep commit, advance branch
12. If DISCARD -> `git reset --hard HEAD~1`
13. Repeat

**NEVER STOP.** Do NOT ask the human if you should continue.
They might be asleep. Run indefinitely until manually stopped.

**Time awareness**: This session has approximately X hours.
Pace yourself for meaningful experiments, not random changes.

**Stuck?**
- Re-read strategy code for new angles
- Read `experiments/results.tsv` for patterns
- Try combining previous near-misses
- Try more radical architectural changes
- Review your Obsidian notes for forgotten ideas
