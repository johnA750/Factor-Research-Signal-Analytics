from __future__ import annotations

import pandas as pd


def select_top_n(scores: pd.Series, top_n: int) -> list[str]:
    """Return tickers with the highest scores."""
    clean_scores = scores.dropna()
    return clean_scores.sort_values(ascending=False).head(top_n).index.tolist()


def equal_weight(tickers: list[str]) -> pd.Series:
    """Assign equal long-only weights."""
    if not tickers:
        return pd.Series(dtype=float)
    return pd.Series(1.0 / len(tickers), index=tickers)


def inverse_volatility_weight(volatility: pd.Series, tickers: list[str]) -> pd.Series:
    """Assign weights proportional to inverse realized volatility."""
    selected = volatility.reindex(tickers).dropna()
    selected = selected[selected > 0]
    if selected.empty:
        return equal_weight(tickers)
    inverse_vol = 1.0 / selected
    return inverse_vol / inverse_vol.sum()

