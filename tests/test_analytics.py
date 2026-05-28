from __future__ import annotations

import pandas as pd

from equity_signal_platform.analytics import max_drawdown, total_return


def test_total_return_compounds_daily_returns() -> None:
    returns = pd.Series([0.10, -0.05, 0.02])
    assert round(total_return(returns), 6) == round((1.10 * 0.95 * 1.02) - 1.0, 6)


def test_max_drawdown_uses_running_peak() -> None:
    equity = pd.Series([100, 120, 90, 110])
    assert max_drawdown(equity) == -0.25

