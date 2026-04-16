> Status: historical
>
> This document is retained for V2 traceability. Start current navigation at `docs/index.md` and current execution-spec navigation at `specs/index.md`.

# Overfit Defense Knowledge Base

## Purpose

This note captures the practical guidance behind the Sprint 2 validation tools so future strategy work can use them consistently instead of re-deriving the rules from code.

## Newey-West Sharpe

- Use Newey-West Sharpe when evaluating minute-bar or otherwise autocorrelated return streams.
- The adjustment replaces naive volatility with a lag-aware variance estimate using Bartlett weights.
- In this repo, `SCORE` is already Newey-West adjusted in the core backtester.
- `NW_SHARPE_BIAS = NAIVE_SHARPE - SCORE` is the quick diagnostic for serial-correlation distortion.
- Large positive bias means the naive Sharpe was overstating signal quality.

## Deflated Sharpe Ratio

- Deflated Sharpe Ratio adjusts for multiple testing and non-normal returns.
- It should be interpreted as a probability-like significance measure in `[0, 1]`.
- Low DSR after many experiments means the best result may be selection luck rather than real alpha.
- In this repo, DSR is advisory rather than a hard reject rule.

## CPCV

- Combinatorial Purged Cross-Validation produces a distribution of out-of-sample Sharpes rather than a single walk-forward number.
- The time axis is split into contiguous groups and every `C(N, k)` test-group combination becomes a path.
- Purging removes training bars adjacent to test boundaries so nearby observations cannot leak into the signal context.
- Embargo trims edge bars from the selected test groups to keep additional distance from boundary effects.
- Interpret `pct_positive` as the share of paths with Sharpe above zero:
  - `> 0.80`: strong
  - `0.60 - 0.80`: moderate
  - `< 0.60`: weak

## Regime Analysis

- Regime analysis checks whether the strategy only works in one market environment.
- The repo uses a simple 4-quadrant classifier:
  - `bull_quiet`
  - `bull_volatile`
  - `bear_quiet`
  - `bear_volatile`
- Each regime reports Newey-West Sharpe, cumulative return, bar count, and win rate.
- If profits are concentrated in one regime, the strategy is less robust than the headline Sharpe suggests.

## Parameter Stability

- Parameter stability checks whether small perturbations around the default settings preserve most of the strategy quality.
- Numeric `__init__` defaults are treated as tuneable parameters.
- Each parameter is swept across a symmetric range, and stability is the fraction of tested values that remain above 50% of peak Sharpe.
- Useful interpretation:
  - `>= 0.70`: good
  - `0.50 - 0.70`: moderate
  - `< 0.50`: poor
- Strategies with no numeric parameters should report `no tuneable parameters` instead of failing.

## Practical Guidance

- Run CPCV after a meaningful `SCORE` improvement or before treating a result as credible.
- Run regime analysis when a strategy appears strong but may be tied to a specific trend or volatility state.
- Run parameter stability after changing thresholds, lookbacks, windows, or any hyperparameters the strategy depends on.
- Do not compare Sprint 2 outputs directly with old Monte Carlo `P_VALUE` workflows. That path is intentionally removed.

## References

- Andrew W. Lo, "The Statistics of Sharpe Ratios", Financial Analysts Journal, 2002
- David H. Bailey and Marcos Lopez de Prado, "The Deflated Sharpe Ratio", Journal of Portfolio Management, 2014
- Marcos Lopez de Prado, *Advances in Financial Machine Learning*, Chapter 12, 2018
- Campbell R. Harvey, Yan Liu, and Heqing Zhu, "... and the Cross-Section of Expected Returns", Review of Financial Studies, 2016
