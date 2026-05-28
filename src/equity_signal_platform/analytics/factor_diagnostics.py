from __future__ import annotations

import pandas as pd


def forward_returns(prices: pd.DataFrame, periods: int = 21) -> pd.DataFrame:
    """Forward simple returns over a fixed horizon."""
    return prices.shift(-periods) / prices - 1.0


def information_coefficient(signal: pd.DataFrame, fwd_returns: pd.DataFrame) -> pd.Series:
    """Daily Spearman rank correlation between signal and forward returns."""
    aligned_signal, aligned_returns = signal.align(fwd_returns, join="inner", axis=0)
    signal_rank = aligned_signal.rank(axis=1)
    return_rank = aligned_returns.rank(axis=1)
    ic = signal_rank.corrwith(return_rank, axis=1)
    ic.name = "information_coefficient"
    return ic


def mean_information_coefficients(
    factors: dict[str, pd.DataFrame],
    prices: pd.DataFrame,
    forward_return_days: int = 21,
) -> pd.DataFrame:
    """Compute mean IC only, used for fast walk-forward training."""
    fwd = forward_returns(prices, forward_return_days)
    rows = []
    for name, signal in factors.items():
        if name == "composite":
            continue
        ic = information_coefficient(signal, fwd)
        rows.append({"factor": name, "mean_ic": ic.mean(skipna=True)})
    return pd.DataFrame(rows).set_index("factor")


def hit_rate(signal: pd.DataFrame, fwd_returns: pd.DataFrame) -> float:
    """Share of dates where top-half ranked names beat bottom-half names."""
    hits = []
    aligned_signal, aligned_returns = signal.align(fwd_returns, join="inner", axis=0)
    for date in aligned_signal.index:
        day_signal = aligned_signal.loc[date].dropna()
        day_returns = aligned_returns.loc[date].reindex(day_signal.index).dropna()
        day_signal = day_signal.reindex(day_returns.index)
        if len(day_signal) < 4:
            continue
        median = day_signal.median()
        top = day_returns[day_signal >= median].mean()
        bottom = day_returns[day_signal < median].mean()
        hits.append(top > bottom)
    return float(pd.Series(hits).mean()) if hits else 0.0


def signal_persistence(signal: pd.DataFrame, lags: list[int]) -> pd.Series:
    """Average cross-sectional rank autocorrelation by lag."""
    results = {}
    ranked = signal.rank(axis=1, pct=True)
    for lag in lags:
        correlations = []
        for date in ranked.index[lag:]:
            current = ranked.loc[date]
            previous = ranked.shift(lag).loc[date]
            joined = pd.concat([current.rename("current"), previous.rename("previous")], axis=1).dropna()
            if len(joined) >= 3:
                correlations.append(joined["current"].corr(joined["previous"], method="spearman"))
        results[f"lag_{lag}"] = pd.Series(correlations).mean() if correlations else pd.NA
    return pd.Series(results, name="signal_persistence")


def cross_sectional_dispersion(signal: pd.DataFrame) -> pd.Series:
    """Cross-sectional standard deviation of signal scores through time."""
    return signal.std(axis=1).rename("cross_sectional_dispersion")


def factor_decay(signal: pd.DataFrame, prices: pd.DataFrame, periods: list[int]) -> pd.Series:
    """Mean IC across multiple forward-return horizons."""
    results = {}
    for period in periods:
        ic = information_coefficient(signal, forward_returns(prices, period))
        results[f"{period}d"] = ic.mean(skipna=True)
    return pd.Series(results, name="factor_decay")


def factor_diagnostic_summary(
    factors: dict[str, pd.DataFrame],
    prices: pd.DataFrame,
    forward_return_days: int = 21,
    decay_periods: list[int] | None = None,
    persistence_lags: list[int] | None = None,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame | pd.Series]]:
    """Summarize factor quality with IC, hit rate, decay, persistence, and dispersion."""
    decay_periods = decay_periods or [1, 5, 10, 21, 63]
    persistence_lags = persistence_lags or [1, 5, 21, 63]
    fwd = forward_returns(prices, forward_return_days)
    rows = []
    details: dict[str, pd.DataFrame | pd.Series] = {}

    for name, signal in factors.items():
        if name == "composite":
            continue
        ic = information_coefficient(signal, fwd)
        dispersion = cross_sectional_dispersion(signal)
        decay = factor_decay(signal, prices, decay_periods)
        persistence = signal_persistence(signal, persistence_lags)
        rows.append(
            {
                "factor": name,
                "mean_ic": ic.mean(skipna=True),
                "ic_volatility": ic.std(skipna=True),
                "ic_positive_rate": (ic.dropna() > 0).mean(),
                "hit_rate": hit_rate(signal, fwd),
                "average_dispersion": dispersion.mean(skipna=True),
            }
        )
        details[name] = pd.concat(
            [
                decay.rename("factor_decay"),
                persistence.rename("signal_persistence"),
            ],
            axis=0,
        )

    return pd.DataFrame(rows).set_index("factor"), details
