from __future__ import annotations

import numpy as np
import pandas as pd

from equity_signal_platform.signals.scoring import combine_factor_scores


def momentum(prices: pd.DataFrame, lookback_days: int = 252, skip_days: int = 21) -> pd.DataFrame:
    """Trailing return excluding the most recent period."""
    past = prices.shift(skip_days)
    return past / past.shift(lookback_days) - 1.0


def volatility(returns: pd.DataFrame, lookback_days: int = 63) -> pd.DataFrame:
    """Annualized trailing realized volatility."""
    return returns.rolling(lookback_days).std() * np.sqrt(252)


def trend(prices: pd.DataFrame, window_days: int = 200) -> pd.DataFrame:
    """Price distance from a moving average."""
    moving_average = prices.rolling(window_days).mean()
    return prices / moving_average - 1.0


def mean_reversion(prices: pd.DataFrame, lookback_days: int = 21) -> pd.DataFrame:
    """Short-term trailing return used as a contrarian signal."""
    return prices / prices.shift(lookback_days) - 1.0


def _cross_sectional_rank(signal: pd.DataFrame, higher_is_better: bool) -> pd.DataFrame:
    ascending = not higher_is_better
    return signal.rank(axis=1, pct=True, ascending=ascending)


def compute_factor_scores(prices: pd.DataFrame, config: dict | None = None) -> dict[str, pd.DataFrame]:
    """Compute individual factor scores and a composite cross-sectional score."""
    config = config or {}
    returns = prices.pct_change()

    raw_momentum = momentum(
        prices,
        lookback_days=config.get("momentum_lookback_days", 252),
        skip_days=config.get("momentum_skip_days", 21),
    )
    raw_volatility = volatility(
        returns,
        lookback_days=config.get("volatility_lookback_days", 63),
    )
    raw_trend = trend(prices, window_days=config.get("trend_window_days", 200))
    raw_mean_reversion = mean_reversion(
        prices,
        lookback_days=config.get("mean_reversion_lookback_days", 21),
    )

    ranked = {
        "momentum": _cross_sectional_rank(raw_momentum, higher_is_better=True),
        "volatility": _cross_sectional_rank(raw_volatility, higher_is_better=False),
        "trend": _cross_sectional_rank(raw_trend, higher_is_better=True),
        "mean_reversion": _cross_sectional_rank(raw_mean_reversion, higher_is_better=False),
    }
    composite = combine_factor_scores(ranked, config.get("factor_weights"))
    ranked["composite"] = composite
    return ranked
