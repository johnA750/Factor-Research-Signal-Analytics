from __future__ import annotations

import pandas as pd
import pytest

from equity_signal_platform.backtesting import run_backtest


def test_backtest_applies_rebalance_weights_after_signal_day() -> None:
    index = pd.bdate_range("2024-01-29", periods=8)
    prices = pd.DataFrame(
        {
            "AAA": [100, 100, 100, 110, 121, 121, 121, 121],
            "BBB": [100, 100, 100, 100, 100, 100, 100, 100],
        },
        index=index,
    )
    scores = pd.DataFrame({"AAA": 1.0, "BBB": 0.0}, index=index)
    vol = pd.DataFrame({"AAA": 0.2, "BBB": 0.2}, index=index)

    result = run_backtest(
        prices=prices,
        scores=scores,
        volatility=vol,
        top_n=1,
        weighting="equal",
        rebalance_frequency="ME",
        transaction_cost_bps=0,
        slippage_bps=0,
    )

    rebalance_day = pd.Timestamp("2024-01-31")
    next_day = pd.Timestamp("2024-02-01")

    assert result.weights.loc[rebalance_day, "AAA"] == 0.0
    assert result.weights.loc[next_day, "AAA"] == 1.0
    assert result.returns.loc[next_day] == pytest.approx(0.10)
