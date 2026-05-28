from __future__ import annotations

import numpy as np
import pandas as pd


def generate_demo_prices(tickers: list[str], start: str = "2018-01-01") -> pd.DataFrame:
    """Create deterministic synthetic prices for quick dashboard demos."""
    dates = pd.bdate_range(start=start, periods=1_600)
    rng = np.random.default_rng(42)
    market_returns = rng.normal(0.00035, 0.010, len(dates))

    prices = {}
    for index, ticker in enumerate(tickers):
        beta = 0.65 + (index % 7) * 0.08
        drift = 0.00005 * ((index % 5) - 2)
        idiosyncratic = rng.normal(0.0, 0.012 + (index % 4) * 0.002, len(dates))
        returns = drift + beta * market_returns + idiosyncratic
        if ticker == "SPY":
            returns = market_returns
        prices[ticker] = 100.0 * np.cumprod(1.0 + returns)

    return pd.DataFrame(prices, index=dates)

