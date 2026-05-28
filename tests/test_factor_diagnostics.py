from __future__ import annotations

import pandas as pd
import pytest

from equity_signal_platform.analytics import forward_returns, information_coefficient, signal_persistence


def test_forward_returns_uses_future_prices() -> None:
    prices = pd.DataFrame({"A": [100, 110, 121], "B": [100, 100, 100]})
    result = forward_returns(prices, periods=1)
    assert result.loc[0, "A"] == pytest.approx(0.10)
    assert result.loc[0, "B"] == 0.0


def test_information_coefficient_is_spearman_rank_correlation() -> None:
    signal = pd.DataFrame({"A": [3], "B": [2], "C": [1]}, index=pd.to_datetime(["2024-01-01"]))
    fwd = pd.DataFrame({"A": [0.03], "B": [0.02], "C": [0.01]}, index=signal.index)
    ic = information_coefficient(signal, fwd)
    assert ic.iloc[0] == 1.0


def test_signal_persistence_reports_rank_autocorrelation() -> None:
    signal = pd.DataFrame(
        {"A": [1, 1, 3], "B": [2, 2, 2], "C": [3, 3, 1]},
        index=pd.date_range("2024-01-01", periods=3),
    )
    persistence = signal_persistence(signal, [1])
    assert persistence["lag_1"] < 1.0
