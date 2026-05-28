from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_sharpe(
    returns: pd.Series,
    window: int = 126,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> pd.Series:
    daily_rf = risk_free_rate / periods_per_year
    excess = returns - daily_rf
    rolling_mean = excess.rolling(window).mean()
    rolling_std = excess.rolling(window).std(ddof=0)
    return rolling_mean / rolling_std * np.sqrt(periods_per_year)


def rolling_volatility(
    returns: pd.Series,
    window: int = 126,
    periods_per_year: int = 252,
) -> pd.Series:
    return returns.rolling(window).std(ddof=0) * np.sqrt(periods_per_year)


def rolling_drawdown(equity_curve: pd.Series, window: int = 126) -> pd.Series:
    rolling_peak = equity_curve.rolling(window, min_periods=1).max()
    return equity_curve / rolling_peak - 1.0


def rolling_turnover(turnover: pd.Series, window: int = 126) -> pd.Series:
    return turnover.rolling(window).mean()


def rolling_metrics(
    returns: pd.Series,
    equity_curve: pd.Series,
    turnover: pd.Series,
    window: int = 126,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "rolling_sharpe": rolling_sharpe(returns, window, risk_free_rate),
            "rolling_volatility": rolling_volatility(returns, window),
            "rolling_drawdown": rolling_drawdown(equity_curve, window),
            "rolling_turnover": rolling_turnover(turnover, window),
        }
    )
