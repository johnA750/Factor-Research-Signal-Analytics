from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from equity_signal_platform.analytics.factor_diagnostics import mean_information_coefficients
from equity_signal_platform.backtesting.engine import run_backtest
from equity_signal_platform.signals import combine_factor_scores, factor_weights_from_ic


@dataclass(frozen=True)
class WalkForwardResult:
    returns: pd.Series
    equity_curve: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    costs: pd.Series
    windows: pd.DataFrame
    factor_weights: pd.DataFrame


def _window_bounds(
    index: pd.DatetimeIndex,
    train_months: int,
    test_months: int,
) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    monthly_dates = pd.Series(index=index, data=index).resample("ME").last().dropna()
    bounds = []
    start = 0
    while start + train_months + test_months <= len(monthly_dates):
        train_start = monthly_dates.iloc[start]
        train_end = monthly_dates.iloc[start + train_months - 1]
        test_start = monthly_dates.iloc[start + train_months]
        test_end = monthly_dates.iloc[start + train_months + test_months - 1]
        bounds.append((train_start, train_end, test_start, test_end))
        start += test_months
    return bounds


def run_walk_forward(
    prices: pd.DataFrame,
    factors: dict[str, pd.DataFrame],
    volatility: pd.DataFrame,
    train_months: int = 36,
    test_months: int = 12,
    min_train_observations: int = 252,
    top_n: int = 8,
    weighting: str = "inverse_volatility",
    rebalance_frequency: str = "ME",
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    initial_capital: float = 100_000.0,
) -> WalkForwardResult:
    """Run rolling train/test windows using train-period ICs to weight factors."""
    returns_parts = []
    weight_parts = []
    turnover_parts = []
    cost_parts = []
    window_rows = []
    factor_weight_rows = []

    for window_number, (train_start, train_end, test_start, test_end) in enumerate(
        _window_bounds(prices.index, train_months, test_months),
        start=1,
    ):
        train_prices = prices.loc[train_start:train_end]
        test_prices = prices.loc[test_start:test_end]
        if len(train_prices) < min_train_observations or test_prices.empty:
            continue

        train_factors = {name: value.loc[train_start:train_end] for name, value in factors.items()}
        ic_summary = mean_information_coefficients(train_factors, train_prices)
        learned_weights = factor_weights_from_ic(ic_summary)

        test_factors = {name: value.loc[test_start:test_end] for name, value in factors.items()}
        test_scores = combine_factor_scores(test_factors, learned_weights)
        result = run_backtest(
            prices=test_prices,
            scores=test_scores,
            volatility=volatility.loc[test_start:test_end],
            top_n=top_n,
            weighting=weighting,
            rebalance_frequency=rebalance_frequency,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
            initial_capital=initial_capital,
        )

        returns_parts.append(result.returns)
        weight_parts.append(result.weights)
        turnover_parts.append(result.turnover)
        cost_parts.append(result.costs)
        window_rows.append(
            {
                "window": window_number,
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
                "test_observations": len(test_prices),
            }
        )
        factor_weight_rows.append({"window": window_number, **learned_weights})

    if not returns_parts:
        empty_index = prices.index[:0]
        return WalkForwardResult(
            returns=pd.Series(dtype=float, name="strategy_return"),
            equity_curve=pd.Series(dtype=float, name="equity_curve"),
            weights=pd.DataFrame(index=empty_index, columns=prices.columns),
            turnover=pd.Series(dtype=float, name="turnover"),
            costs=pd.Series(dtype=float, name="costs"),
            windows=pd.DataFrame(),
            factor_weights=pd.DataFrame(),
        )

    out_returns = pd.concat(returns_parts).sort_index()
    out_returns = out_returns[~out_returns.index.duplicated(keep="first")]
    equity_curve = initial_capital * (1.0 + out_returns).cumprod()
    equity_curve.name = "equity_curve"

    return WalkForwardResult(
        returns=out_returns.rename("strategy_return"),
        equity_curve=equity_curve,
        weights=pd.concat(weight_parts).sort_index(),
        turnover=pd.concat(turnover_parts).sort_index().rename("turnover"),
        costs=pd.concat(cost_parts).sort_index().rename("costs"),
        windows=pd.DataFrame(window_rows),
        factor_weights=pd.DataFrame(factor_weight_rows).set_index("window"),
    )
