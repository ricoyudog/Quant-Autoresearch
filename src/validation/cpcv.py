import itertools
from typing import Sequence

import numpy as np
import pandas as pd

from validation.newey_west import newey_west_sharpe


def generate_cpcv_paths(n_groups: int, n_test: int) -> list[tuple[int, ...]]:
    """Generate all CPCV test-group combinations."""
    if n_groups <= 0:
        raise ValueError("n_groups must be positive")
    if n_test <= 0 or n_test > n_groups:
        raise ValueError("n_test must be between 1 and n_groups")

    return list(itertools.combinations(range(n_groups), n_test))


def build_group_slices(length: int, n_groups: int) -> list[range]:
    """Split an index range into contiguous CPCV groups."""
    if length <= 0:
        raise ValueError("length must be positive")
    if n_groups <= 0 or n_groups > length:
        raise ValueError("n_groups must be between 1 and length")

    index_groups = np.array_split(np.arange(length), n_groups)
    group_slices = []
    for indices in index_groups:
        start = int(indices[0])
        stop = int(indices[-1]) + 1
        group_slices.append(range(start, stop))
    return group_slices


def resolve_train_test_indices(
    group_slices: Sequence[range],
    test_groups: tuple[int, ...],
    purge_bars: int = 390,
    embargo_bars: int = 0,
) -> tuple[list[int], list[int]]:
    """Resolve train/test indices for a CPCV path with purge and embargo."""
    test_group_set = set(test_groups)
    raw_test_indices: list[int] = []
    train_indices: list[int] = []

    for group_index, group_slice in enumerate(group_slices):
        group_values = list(group_slice)
        if group_index in test_group_set:
            trimmed = group_values[embargo_bars:]
            if embargo_bars > 0:
                trimmed = trimmed[: len(trimmed) - embargo_bars]
            raw_test_indices.extend(trimmed)
        else:
            train_indices.extend(group_values)

    purge_set = set()
    for test_group in test_groups:
        test_slice = group_slices[test_group]
        start = test_slice.start
        stop = test_slice.stop
        for index in range(max(0, start - purge_bars), start):
            purge_set.add(index)
        for index in range(stop, stop + purge_bars):
            purge_set.add(index)

    filtered_train = [index for index in train_indices if index not in purge_set]
    filtered_test = sorted(set(raw_test_indices))
    return filtered_train, filtered_test


def _evaluate_cpcv_path(
    strategy_class,
    data_config: dict[str, pd.DataFrame],
    train_indices: Sequence[int],
    test_indices: Sequence[int],
) -> float:
    """Evaluate a single CPCV path over the provided test indices."""
    if not test_indices:
        return 0.0

    all_returns = []
    visible_indices = sorted(set(train_indices).union(test_indices))

    for _, df in data_config.items():
        if df is None or df.empty:
            continue

        valid_visible_indices = [index for index in visible_indices if index < len(df)]
        if not valid_visible_indices:
            continue

        history_df = df.iloc[valid_visible_indices].copy()
        if history_df.empty:
            continue

        visible_position_map = {
            original_index: position for position, original_index in enumerate(valid_visible_indices)
        }

        # Build lagged positions causally so each test bar only sees prior visible bars.
        lagged_values = [0.0]
        for visible_position in range(1, len(valid_visible_indices)):
            prefix_indices = valid_visible_indices[:visible_position]
            prefix_df = df.iloc[prefix_indices].copy()
            if prefix_df.empty:
                lagged_values.append(0.0)
                continue

            prefix_signals = strategy_class().generate_signals(prefix_df)
            if not isinstance(prefix_signals, pd.Series):
                prefix_signals = pd.Series(prefix_signals, index=prefix_df.index)

            prefix_signals = prefix_signals.reindex(prefix_df.index).fillna(0)
            lagged_values.append(float(prefix_signals.iloc[-1]))

        lagged_signals = pd.Series(lagged_values, index=history_df.index, dtype=float)

        valid_test_labels = [index for index in test_indices if index in visible_position_map]
        if not valid_test_labels:
            continue

        history_positions = [
            visible_position_map[original_index] for original_index in valid_test_labels
        ]

        path_returns = history_df.iloc[history_positions]["returns"]
        path_signals = lagged_signals.iloc[history_positions]
        trades = lagged_signals.diff().abs().fillna(0).iloc[history_positions]
        volatility = history_df.iloc[history_positions].get(
            "volatility", pd.Series(0.0, index=path_returns.index)
        )
        slippage = pd.Series(volatility, index=path_returns.index).fillna(0) * 0.1
        costs = trades * (0.0005 + slippage)
        net_returns = path_returns * path_signals - costs
        all_returns.append(net_returns)

    if not all_returns:
        return 0.0

    combined_returns = pd.concat(all_returns, axis=1).mean(axis=1).fillna(0)
    return float(newey_west_sharpe(combined_returns))


def run_cpcv(
    strategy_class,
    data_config: dict[str, pd.DataFrame],
    n_groups: int = 8,
    n_test: int = 2,
    purge_bars: int = 390,
    embargo_bars: int = 0,
) -> dict[str, float | list[float]]:
    """Run combinatorial purged cross-validation over cached market data."""
    if not data_config:
        raise ValueError("data_config must not be empty")

    usable_frames = [df for df in data_config.values() if df is not None and not df.empty]
    if not usable_frames:
        raise ValueError("data_config must contain at least one dataframe")

    min_length = min(len(df) for df in usable_frames)
    group_slices = build_group_slices(min_length, n_groups)
    path_sharpes = []

    for test_groups in generate_cpcv_paths(n_groups, n_test):
        train_indices, test_indices = resolve_train_test_indices(
            group_slices=group_slices,
            test_groups=test_groups,
            purge_bars=purge_bars,
            embargo_bars=embargo_bars,
        )
        path_sharpes.append(
            _evaluate_cpcv_path(strategy_class, data_config, train_indices, test_indices)
        )

    sharpes = np.array(path_sharpes, dtype=float)
    return {
        "sharpe_distribution": sharpes.tolist(),
        "mean_sharpe": float(sharpes.mean()) if len(sharpes) else 0.0,
        "std_sharpe": float(sharpes.std()) if len(sharpes) else 0.0,
        "pct_positive": float(np.mean(sharpes > 0)) if len(sharpes) else 0.0,
        "worst_sharpe": float(sharpes.min()) if len(sharpes) else 0.0,
        "best_sharpe": float(sharpes.max()) if len(sharpes) else 0.0,
    }
