from __future__ import annotations

import pandas as pd
import statsmodels.api as sm


def capm_regression(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> pd.Series:
    """Estimate CAPM alpha and beta using daily excess returns."""
    daily_rf = risk_free_rate / periods_per_year
    data = pd.concat(
        [
            (strategy_returns - daily_rf).rename("strategy_excess"),
            (benchmark_returns - daily_rf).rename("market_excess"),
        ],
        axis=1,
    ).dropna()
    if len(data) < 3:
        return pd.Series(dtype=float)

    model = sm.OLS(data["strategy_excess"], sm.add_constant(data["market_excess"])).fit()
    daily_alpha = model.params["const"]
    return pd.Series(
        {
            "annualized_alpha": daily_alpha * periods_per_year,
            "beta": model.params["market_excess"],
            "r_squared": model.rsquared,
            "alpha_t_stat": model.tvalues["const"],
            "beta_t_stat": model.tvalues["market_excess"],
        },
        name="capm_regression",
    )


def factor_regression(
    strategy_returns: pd.Series,
    factor_returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> pd.Series:
    """Generic factor regression. Use Fama-French returns if supplied by the user."""
    daily_rf = risk_free_rate / periods_per_year
    data = pd.concat([(strategy_returns - daily_rf).rename("strategy_excess"), factor_returns], axis=1).dropna()
    if len(data) < len(factor_returns.columns) + 2:
        return pd.Series(dtype=float)

    model = sm.OLS(data["strategy_excess"], sm.add_constant(data[factor_returns.columns])).fit()
    output = {
        "annualized_alpha": model.params["const"] * periods_per_year,
        "r_squared": model.rsquared,
        "alpha_t_stat": model.tvalues["const"],
    }
    for column in factor_returns.columns:
        output[f"{column}_beta"] = model.params[column]
        output[f"{column}_t_stat"] = model.tvalues[column]
    return pd.Series(output, name="factor_regression")
