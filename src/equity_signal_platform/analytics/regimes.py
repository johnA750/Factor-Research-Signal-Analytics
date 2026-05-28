from __future__ import annotations

import numpy as np
import pandas as pd

from equity_signal_platform.analytics.metrics import performance_summary


def classify_market_regimes(
    benchmark_prices: pd.Series,
    moving_average_days: int = 200,
    volatility_lookback_days: int = 21,
    volatility_quantile_window: int = 252,
    high_volatility_quantile: float = 0.60,
) -> pd.DataFrame:
    """Classify dates into trend and volatility regimes using a benchmark series."""
    benchmark_prices = benchmark_prices.dropna().sort_index()
    returns = benchmark_prices.pct_change()
    moving_average = benchmark_prices.rolling(moving_average_days).mean()
    realized_vol = returns.rolling(volatility_lookback_days).std() * np.sqrt(252)
    min_vol_observations = min(60, volatility_quantile_window)
    vol_threshold = realized_vol.rolling(
        volatility_quantile_window,
        min_periods=min_vol_observations,
    ).quantile(high_volatility_quantile)

    regimes = pd.DataFrame(index=benchmark_prices.index)
    regimes["market_regime"] = np.where(benchmark_prices >= moving_average, "bull", "bear")
    regimes.loc[moving_average.isna(), "market_regime"] = pd.NA
    regimes["volatility_regime"] = np.where(realized_vol >= vol_threshold, "high_volatility", "low_volatility")
    regimes.loc[vol_threshold.isna(), "volatility_regime"] = pd.NA
    regimes["combined_regime"] = regimes["market_regime"].astype("string") + "_" + regimes["volatility_regime"].astype("string")
    return regimes


def performance_by_regime(
    returns: pd.Series,
    equity_curve: pd.Series,
    turnover: pd.Series,
    regimes: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Evaluate strategy performance grouped by market and volatility regimes."""
    returns_col = "strategy_return"
    equity_col = "equity_curve"
    turnover_col = "turnover"
    aligned = pd.concat(
        [
            returns.rename(returns_col),
            equity_curve.rename(equity_col),
            turnover.rename(turnover_col),
            regimes,
        ],
        axis=1,
    ).dropna(subset=[returns_col])
    outputs = {}

    for regime_col in ["market_regime", "volatility_regime", "combined_regime"]:
        rows = []
        for regime_name, group in aligned.dropna(subset=[regime_col]).groupby(regime_col):
            group_returns = group[returns_col]
            group_equity = (1.0 + group_returns).cumprod()
            summary = performance_summary(group_returns, group_equity, group[turnover_col])
            summary["observations"] = len(group)
            rows.append(summary.rename(regime_name))
        outputs[regime_col] = pd.DataFrame(rows)

    return outputs
