from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


def download_adjusted_prices(
    tickers: list[str],
    start: str,
    end: str | None = None,
    auto_adjust: bool = True,
    cache_path: str | Path | None = None,
) -> pd.DataFrame:
    """Download adjusted close prices from Yahoo Finance.

    The function returns a wide DataFrame indexed by date with tickers as columns.
    """
    if cache_path:
        cache_file = Path(cache_path)
        if cache_file.exists():
            cached_prices = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            missing_tickers = sorted(set(tickers) - set(cached_prices.columns))
            if not missing_tickers:
                return cached_prices

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=auto_adjust,
        progress=False,
        group_by="column",
    )

    if raw.empty:
        raise ValueError("No price data returned from yfinance.")

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"]
        elif "Adj Close" in raw.columns.get_level_values(0):
            prices = raw["Adj Close"]
        else:
            raise ValueError("Could not find close prices in yfinance response.")
    else:
        price_col = "Close" if "Close" in raw.columns else "Adj Close"
        prices = raw[[price_col]].rename(columns={price_col: tickers[0]})

    prices = prices.sort_index().dropna(axis=1, how="all")
    prices = prices.ffill().dropna(how="all")

    if cache_path:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        prices.to_csv(cache_file)

    return prices
