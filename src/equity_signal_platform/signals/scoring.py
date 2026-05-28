from __future__ import annotations

import pandas as pd


FACTOR_COLUMNS = ["momentum", "volatility", "trend", "mean_reversion"]


def combine_factor_scores(
    factors: dict[str, pd.DataFrame],
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Combine ranked factor DataFrames into one composite score."""
    available = [name for name in FACTOR_COLUMNS if name in factors]
    if not available:
        raise ValueError("No factor scores were provided.")

    if weights is None:
        weights = {name: 1.0 / len(available) for name in available}

    cleaned = pd.Series({name: float(weights.get(name, 0.0)) for name in available})
    if cleaned.abs().sum() == 0:
        cleaned = pd.Series(1.0, index=available)
    cleaned = cleaned / cleaned.abs().sum()

    composite = sum(factors[name] * cleaned[name] for name in available)
    return composite


def factor_weights_from_ic(ic_summary: pd.DataFrame) -> dict[str, float]:
    """Estimate long-only factor weights from positive historical IC values."""
    if "mean_ic" not in ic_summary.columns:
        raise ValueError("IC summary must contain a mean_ic column.")

    positive_ic = ic_summary["mean_ic"].clip(lower=0.0)
    if positive_ic.sum() == 0:
        return {factor: 1.0 / len(positive_ic) for factor in positive_ic.index}
    return (positive_ic / positive_ic.sum()).to_dict()
