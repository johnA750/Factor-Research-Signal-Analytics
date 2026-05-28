from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from equity_signal_platform.portfolio import equal_weight, inverse_volatility_weight, select_top_n


@dataclass(frozen=True)
class BacktestResult:
    returns: pd.Series
    equity_curve: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    costs: pd.Series


def _rebalance_dates(index: pd.DatetimeIndex, frequency: str) -> pd.DatetimeIndex:
    dates = pd.Series(index=index, data=index)
    return pd.DatetimeIndex(dates.resample(frequency).last().dropna().values)


def run_backtest(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    volatility: pd.DataFrame,
    top_n: int = 8,
    weighting: str = "inverse_volatility",
    rebalance_frequency: str = "ME",
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Run a monthly long-only factor backtest with costs.

    Rebalance-day signals are used to set holdings for the following trading day.
    """
    prices = prices.sort_index()
    returns = prices.pct_change().fillna(0.0)
    scores = scores.reindex_like(prices)
    volatility = volatility.reindex_like(prices)

    target_weights = pd.DataFrame(pd.NA, index=prices.index, columns=prices.columns, dtype="Float64")
    turnover = pd.Series(0.0, index=prices.index, name="turnover")
    costs = pd.Series(0.0, index=prices.index, name="costs")
    previous_weights = pd.Series(0.0, index=prices.columns)
    cost_rate = (transaction_cost_bps + slippage_bps) / 10_000.0

    for rebalance_date in _rebalance_dates(prices.index, rebalance_frequency):
        day_scores = scores.loc[rebalance_date]
        selected = select_top_n(day_scores, top_n=top_n)

        if weighting == "equal":
            new_weights = equal_weight(selected)
        elif weighting == "inverse_volatility":
            new_weights = inverse_volatility_weight(volatility.loc[rebalance_date], selected)
        else:
            raise ValueError(f"Unsupported weighting method: {weighting}")

        full_weights = pd.Series(0.0, index=prices.columns)
        full_weights.loc[new_weights.index] = new_weights
        target_weights.loc[rebalance_date] = full_weights

        day_turnover = (full_weights - previous_weights).abs().sum()
        turnover.loc[rebalance_date] = day_turnover
        costs.loc[rebalance_date] = day_turnover * cost_rate
        previous_weights = full_weights

    daily_weights = target_weights.ffill().fillna(0.0).astype(float)
    applied_weights = daily_weights.shift(1).fillna(0.0)
    strategy_returns = (applied_weights * returns).sum(axis=1) - costs
    equity_curve = initial_capital * (1.0 + strategy_returns).cumprod()
    equity_curve.name = "equity_curve"
    strategy_returns.name = "strategy_return"

    return BacktestResult(
        returns=strategy_returns,
        equity_curve=equity_curve,
        weights=applied_weights,
        turnover=turnover,
        costs=costs,
    )
