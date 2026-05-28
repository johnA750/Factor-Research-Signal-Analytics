from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from equity_signal_platform.analytics import (
    capm_regression,
    classify_market_regimes,
    factor_diagnostic_summary,
    performance_by_regime,
    performance_summary,
    rolling_metrics,
)
from equity_signal_platform.backtesting import run_backtest, run_walk_forward
from equity_signal_platform.signals import compute_factor_scores


@dataclass(frozen=True)
class ExperimentResult:
    name: str
    summary: pd.Series
    returns: pd.Series
    equity_curve: pd.Series
    rolling: pd.DataFrame
    metadata: dict[str, Any]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _write_frame(frame: pd.DataFrame | pd.Series, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(frame, pd.Series):
        frame.to_frame("value").to_csv(path)
    else:
        frame.to_csv(path)


def run_single_experiment(
    name: str,
    description: str,
    config: dict[str, Any],
    prices: pd.DataFrame,
    benchmark_prices: pd.Series | None = None,
) -> ExperimentResult:
    signal_config = config.get("signals", {})
    portfolio_config = config.get("portfolio", {})
    backtest_config = config.get("backtest", {})
    rolling_config = config.get("rolling", {})
    walk_config = config.get("walk_forward", {})

    factors = compute_factor_scores(prices, signal_config)
    result = run_backtest(
        prices=prices,
        scores=factors["composite"],
        volatility=factors["volatility"],
        top_n=portfolio_config.get("top_n", 8),
        weighting=portfolio_config.get("weighting", "inverse_volatility"),
        rebalance_frequency=backtest_config.get("rebalance_frequency", "ME"),
        transaction_cost_bps=backtest_config.get("transaction_cost_bps", 10),
        slippage_bps=backtest_config.get("slippage_bps", 5),
        initial_capital=backtest_config.get("initial_capital", 100_000),
    )
    summary = performance_summary(
        result.returns,
        result.equity_curve,
        result.turnover,
        risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
    )
    rolling = rolling_metrics(
        result.returns,
        result.equity_curve,
        result.turnover,
        window=rolling_config.get("window_days", 126),
        risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
    )

    metadata: dict[str, Any] = {
        "name": name,
        "description": description,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "portfolio": portfolio_config,
        "signals": signal_config,
    }

    experiment_config = config.get("experiments", {})
    if experiment_config.get("include_walk_forward", False) and walk_config:
        walk = run_walk_forward(
            prices=prices,
            factors=factors,
            volatility=factors["volatility"],
            train_months=walk_config.get("train_months", 36),
            test_months=walk_config.get("test_months", 12),
            min_train_observations=walk_config.get("min_train_observations", 252),
            top_n=portfolio_config.get("top_n", 8),
            weighting=portfolio_config.get("weighting", "inverse_volatility"),
            rebalance_frequency=backtest_config.get("rebalance_frequency", "ME"),
            transaction_cost_bps=backtest_config.get("transaction_cost_bps", 10),
            slippage_bps=backtest_config.get("slippage_bps", 5),
            initial_capital=backtest_config.get("initial_capital", 100_000),
        )
        metadata["walk_forward_windows"] = len(walk.windows)
        metadata["walk_forward_summary"] = performance_summary(
            walk.returns,
            walk.equity_curve,
            walk.turnover,
            risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
        ).to_dict()

    if benchmark_prices is not None:
        benchmark_returns = benchmark_prices.pct_change()
        metadata["capm"] = capm_regression(
            result.returns,
            benchmark_returns,
            risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
        ).to_dict()

    if experiment_config.get("include_factor_diagnostics", False):
        factor_summary, _ = factor_diagnostic_summary(
            factors,
            prices,
            forward_return_days=config.get("factor_evaluation", {}).get("forward_return_days", 21),
        )
        metadata["factor_summary"] = factor_summary.to_dict()

    return ExperimentResult(
        name=name,
        summary=summary,
        returns=result.returns,
        equity_curve=result.equity_curve,
        rolling=rolling,
        metadata=metadata,
    )


def run_experiments(
    base_config: dict[str, Any],
    prices: pd.DataFrame,
    benchmark_prices: pd.Series | None = None,
    output_dir: str | Path = "reports/experiments",
) -> pd.DataFrame:
    """Run config-driven experiments and save comparable outputs."""
    output_dir = Path(output_dir)
    definitions = base_config.get("experiments", {}).get("definitions", [])
    rows = []

    for definition in definitions:
        name = definition["name"]
        description = definition.get("description", "")
        overrides = {key: value for key, value in definition.items() if key not in {"name", "description"}}
        experiment_config = _deep_merge(base_config, overrides)
        experiment = run_single_experiment(name, description, experiment_config, prices, benchmark_prices)

        experiment_dir = output_dir / name
        experiment_dir.mkdir(parents=True, exist_ok=True)
        _write_frame(experiment.summary, experiment_dir / "summary.csv")
        _write_frame(experiment.returns, experiment_dir / "returns.csv")
        _write_frame(experiment.equity_curve, experiment_dir / "equity_curve.csv")
        _write_frame(experiment.rolling, experiment_dir / "rolling_metrics.csv")
        with (experiment_dir / "metadata.json").open("w", encoding="utf-8") as file:
            json.dump(experiment.metadata, file, indent=2, default=str)

        row = experiment.summary.to_dict()
        row["experiment"] = name
        row["description"] = description
        rows.append(row)

    comparison = pd.DataFrame(rows).set_index("experiment") if rows else pd.DataFrame()
    if not comparison.empty:
        comparison.to_csv(output_dir / "experiment_comparison.csv")
    return comparison
