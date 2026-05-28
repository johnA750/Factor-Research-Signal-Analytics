from __future__ import annotations

import numpy as np
import pandas as pd


def total_return(returns: pd.Series) -> float:
    return float((1.0 + returns).prod() - 1.0)


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    clean = returns.dropna()
    if clean.empty:
        return 0.0
    cumulative = (1.0 + clean).prod()
    years = len(clean) / periods_per_year
    return float(cumulative ** (1.0 / years) - 1.0) if years > 0 else 0.0


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    return float(returns.std(ddof=0) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    daily_rf = risk_free_rate / periods_per_year
    excess = returns - daily_rf
    vol = excess.std(ddof=0)
    if vol == 0 or np.isnan(vol):
        return 0.0
    return float(excess.mean() / vol * np.sqrt(periods_per_year))


def max_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    return float(drawdown.min())


def performance_summary(
    returns: pd.Series,
    equity_curve: pd.Series,
    turnover: pd.Series,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    return pd.Series(
        {
            "total_return": total_return(returns),
            "annualized_return": annualized_return(returns),
            "annualized_volatility": annualized_volatility(returns),
            "sharpe_ratio": sharpe_ratio(returns, risk_free_rate=risk_free_rate),
            "max_drawdown": max_drawdown(equity_curve),
            "average_rebalance_turnover": turnover[turnover > 0].mean(),
        }
    )

