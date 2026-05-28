from __future__ import annotations

import pandas as pd

from equity_signal_platform.analytics import capm_regression, classify_market_regimes


def test_capm_regression_recovers_positive_beta() -> None:
    benchmark = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02])
    strategy = benchmark * 1.5
    result = capm_regression(strategy, benchmark)
    assert round(result["beta"], 1) == 1.5


def test_classify_market_regimes_returns_expected_columns() -> None:
    prices = pd.Series(range(100, 360), index=pd.bdate_range("2023-01-02", periods=260))
    regimes = classify_market_regimes(
        prices,
        moving_average_days=20,
        volatility_lookback_days=5,
        volatility_quantile_window=20,
    )
    assert {"market_regime", "volatility_regime", "combined_regime"}.issubset(regimes.columns)
    assert regimes["market_regime"].dropna().iloc[-1] == "bull"

