from __future__ import annotations

import pandas as pd


def format_percent(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}%}" if pd.notna(value) else "n/a"


def format_number(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}" if pd.notna(value) else "n/a"


def format_integer(value: int | float) -> str:
    return f"{value:,.0f}" if pd.notna(value) else "n/a"
