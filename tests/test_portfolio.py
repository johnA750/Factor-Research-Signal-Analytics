from __future__ import annotations

import pandas as pd

from equity_signal_platform.portfolio import equal_weight, inverse_volatility_weight, select_top_n


def test_select_top_n_returns_highest_scores() -> None:
    scores = pd.Series({"A": 0.2, "B": 0.9, "C": 0.4})
    assert select_top_n(scores, top_n=2) == ["B", "C"]


def test_equal_weight_sums_to_one() -> None:
    weights = equal_weight(["A", "B", "C"])
    assert weights.sum() == 1.0


def test_inverse_volatility_prefers_lower_volatility() -> None:
    vol = pd.Series({"A": 0.10, "B": 0.20})
    weights = inverse_volatility_weight(vol, ["A", "B"])
    assert weights["A"] > weights["B"]
    assert round(weights.sum(), 10) == 1.0

