from __future__ import annotations

import pandas as pd


def format_percent(value: float) -> str:
    return f"{value:.2%}" if pd.notna(value) else "n/a"


def format_number(value: float) -> str:
    return f"{value:.2f}" if pd.notna(value) else "n/a"


def format_table(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.copy()

