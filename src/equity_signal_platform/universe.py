from __future__ import annotations


STARTER_LARGE_CAP_US = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "JPM",
    "JNJ",
    "V",
    "PG",
    "UNH",
    "HD",
    "MA",
    "XOM",
    "PEP",
    "KO",
    "MRK",
    "ABBV",
    "COST",
    "CRM",
]


def get_universe(config: dict | None = None) -> list[str]:
    """Return configured tickers or the built-in starter large-cap universe."""
    if config and config.get("tickers"):
        return [ticker.upper() for ticker in config["tickers"]]
    return STARTER_LARGE_CAP_US.copy()

