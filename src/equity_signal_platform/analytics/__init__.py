from equity_signal_platform.analytics.metrics import (
    annualized_return,
    annualized_volatility,
    max_drawdown,
    performance_summary,
    sharpe_ratio,
    total_return,
)
from equity_signal_platform.analytics.factor_diagnostics import (
    factor_decay,
    factor_diagnostic_summary,
    forward_returns,
    hit_rate,
    information_coefficient,
    mean_information_coefficients,
    signal_persistence,
)
from equity_signal_platform.analytics.regimes import classify_market_regimes, performance_by_regime
from equity_signal_platform.analytics.regression import capm_regression, factor_regression
from equity_signal_platform.analytics.rolling import rolling_metrics

__all__ = [
    "total_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe_ratio",
    "max_drawdown",
    "performance_summary",
    "rolling_metrics",
    "forward_returns",
    "information_coefficient",
    "mean_information_coefficients",
    "hit_rate",
    "signal_persistence",
    "factor_decay",
    "factor_diagnostic_summary",
    "classify_market_regimes",
    "performance_by_regime",
    "capm_regression",
    "factor_regression",
]
