from __future__ import annotations

import pandas as pd

from equity_signal_platform.backtesting import run_walk_forward
from equity_signal_platform.signals import compute_factor_scores


def test_walk_forward_returns_out_of_sample_series() -> None:
    index = pd.bdate_range("2020-01-01", periods=520)
    prices = pd.DataFrame(
        {
            "AAA": 100 + pd.Series(range(520), index=index) * 0.1,
            "BBB": 100 + pd.Series(range(520), index=index) * 0.05,
            "CCC": 100 - pd.Series(range(520), index=index) * 0.02,
        },
        index=index,
    )
    factors = compute_factor_scores(
        prices,
        {
            "momentum_lookback_days": 20,
            "momentum_skip_days": 2,
            "volatility_lookback_days": 10,
            "trend_window_days": 20,
            "mean_reversion_lookback_days": 5,
        },
    )
    result = run_walk_forward(
        prices=prices,
        factors=factors,
        volatility=factors["volatility"],
        train_months=12,
        test_months=6,
        min_train_observations=100,
        top_n=1,
        weighting="equal",
        transaction_cost_bps=0,
        slippage_bps=0,
    )
    assert not result.returns.empty
    assert not result.windows.empty
    assert not result.factor_weights.empty

