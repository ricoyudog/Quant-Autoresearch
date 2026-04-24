import pandas as pd

import core.backtester as bt
from validation.newey_west import newey_west_sharpe


def _write_strategy_file(tmp_path):
    strategy_path = tmp_path / "strategy.py"
    strategy_path.write_text(
        "class TradingStrategy:\n"
        "    def select_universe(self, daily_data):\n"
        "        return ['TEST']\n"
        "    def generate_signals(self, data):\n"
        "        return pd.Series(1, index=data.index)\n"
    )
    return strategy_path


def _parse_metric(output: str, name: str) -> float:
    for line in output.splitlines():
        if line.startswith(f"{name}:"):
            return float(line.split(":", 1)[1].strip())
    raise AssertionError(f"{name} not found in output:\n{output}")


def _program_markdown_path() -> str:
    return str(bt.CACHE_DIR).replace("data/cache", "program.md")


def _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data: pd.DataFrame) -> None:
    """Satisfy the V2 public minute-runtime preconditions while reusing legacy metric fixtures."""
    daily_frame = pd.DataFrame({"session_date": pd.to_datetime(["2025-01-02"]), "ticker": ["TEST"]})

    monkeypatch.setattr(bt, "load_daily_data", lambda start_date=None, end_date=None: daily_frame.copy())
    monkeypatch.setattr(bt, "load_data", lambda: {"TEST": sample_data})
    monkeypatch.setattr(
        bt,
        "_minute_pipeline_walk_forward_validation",
        lambda strategy_instance, daily_data, universe_size_override: bt._legacy_walk_forward_validation(
            strategy_instance
        ),
    )


def _expected_newey_west_score(sample_data: pd.DataFrame) -> float:
    window_size = len(sample_data) // 5
    window_scores = []

    for i in range(5):
        train_end = int((i + 1) * window_size * 0.7)
        test_start = train_end
        test_end = (i + 1) * window_size

        history_df = sample_data.iloc[:test_end].copy()
        full_signals = pd.Series(1, index=history_df.index).fillna(0)
        signals = full_signals.shift(1).fillna(0).iloc[test_start:test_end]

        test_returns = sample_data.iloc[test_start:test_end]["returns"]
        trades = signals.diff().abs().fillna(0)
        vol = sample_data.iloc[test_start:test_end]["volatility"]
        costs = trades * (0.0005 + vol * 0.1)
        net_returns = (test_returns * signals) - costs
        window_scores.append(newey_west_sharpe(net_returns))

    return sum(window_scores) / len(window_scores)


def test_output_contains_naive_sharpe(tmp_path, sample_data, monkeypatch, capsys):
    """Public V2 entrypoint should still expose the raw Sharpe once minute preconditions are satisfied."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    output = capsys.readouterr().out
    assert "NAIVE_SHARPE:" in output


def test_output_contains_nw_bias(tmp_path, sample_data, monkeypatch, capsys):
    """Public V2 entrypoint should report the NW adjustment gap once minute preconditions are satisfied."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    output = capsys.readouterr().out
    assert "NW_SHARPE_BIAS:" in output


def test_output_contains_deflated_sr(tmp_path, sample_data, monkeypatch, capsys):
    """Public V2 entrypoint should include Deflated Sharpe Ratio once minute preconditions are satisfied."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    output = capsys.readouterr().out
    assert "DEFLATED_SR:" in output


def test_missing_results_tsv_defaults_to_single_trial(tmp_path, sample_data, monkeypatch):
    """Without experiment history, DSR should still default to a single trial via the public V2 entrypoint."""
    strategy_path = _write_strategy_file(tmp_path)
    observed = {}

    def fake_deflated_sharpe_ratio(returns, n_trials, skew=None, kurtosis=None):
        observed["n_trials"] = n_trials
        return 0.5

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)
    monkeypatch.setattr(bt, "deflated_sharpe_ratio", fake_deflated_sharpe_ratio, raising=False)

    bt.walk_forward_validation()

    assert observed["n_trials"] == 1


def test_no_p_value_in_output(tmp_path, sample_data, monkeypatch, capsys):
    """Public V2 entrypoint should not reintroduce the removed Monte Carlo placeholder output."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    output = capsys.readouterr().out
    assert "P_VALUE:" not in output


def test_no_monte_carlo_function():
    """Legacy Monte Carlo helper should no longer exist."""
    assert not hasattr(bt, "monte_carlo_permutation_test")


def test_score_is_newey_west(tmp_path, sample_data, monkeypatch, capsys):
    """Reported SCORE should still match the average Newey-West Sharpe through the public V2 entrypoint."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    output = capsys.readouterr().out
    score = _parse_metric(output, "SCORE")
    expected_score = _expected_newey_west_score(sample_data)

    assert score == round(expected_score, 4)


def test_nw_bias_calculation(tmp_path, sample_data, monkeypatch, capsys):
    """NW bias should equal raw Sharpe minus adjusted SCORE through the public V2 entrypoint."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    output = capsys.readouterr().out
    score = _parse_metric(output, "SCORE")
    naive_sharpe = _parse_metric(output, "NAIVE_SHARPE")
    nw_bias = _parse_metric(output, "NW_SHARPE_BIAS")

    assert nw_bias == round(naive_sharpe - score, 4)


def test_results_tsv_new_columns(tmp_path, sample_data, monkeypatch):
    """Public V2 entrypoint should initialize results.tsv with the Sprint 1 header."""
    strategy_path = _write_strategy_file(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bt, "STRATEGY_FILE", str(strategy_path))
    _enable_public_entrypoint_for_overfit_tests(monkeypatch, sample_data)

    bt.walk_forward_validation()

    results_path = tmp_path / "experiments" / "results.tsv"
    assert results_path.exists()

    header = results_path.read_text().splitlines()[0]
    assert header == (
        "commit\tscore\tnaive_sharpe\tdeflated_sr\tsortino\tcalmar\tdrawdown\tmax_dd_days\t"
        "trades\twin_rate\tprofit_factor\tavg_win\tavg_loss\tbaseline_sharpe\tnw_bias\tstatus\t"
        "description"
    )


def test_baseline_constraint_retained():
    """Program guidance should still discard strategies below the baseline."""
    program_path = bt.os.path.join(bt.os.path.dirname(bt.__file__), "..", "..", "program.md")
    program_text = bt.os.path.abspath(program_path)

    with open(program_text, "r") as handle:
        content = handle.read()

    assert "SCORE > BASELINE_SHARPE" in content
    assert "SCORE <= BASELINE_SHARPE" in content
