from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.bootstrap import ROOT
from dashboard.demo_data import generate_demo_prices

from equity_signal_platform.analytics import (
    capm_regression,
    classify_market_regimes,
    factor_decay,
    factor_diagnostic_summary,
    forward_returns,
    information_coefficient,
    performance_by_regime,
    performance_summary,
    rolling_metrics,
    signal_persistence,
)
from equity_signal_platform.analytics.factor_diagnostics import cross_sectional_dispersion
from equity_signal_platform.backtesting import run_backtest, run_walk_forward
from equity_signal_platform.config import PlatformConfig
from equity_signal_platform.data import download_adjusted_prices
from equity_signal_platform.experiments import run_experiments
from equity_signal_platform.signals import compute_factor_scores, mean_reversion, momentum, trend, volatility
from equity_signal_platform.universe import get_universe


@st.cache_data(show_spinner=False, ttl=3600)
def load_research_context(config_path: str, use_demo_data: bool = True) -> dict:
    """Load prices, run analytics, and return shared dashboard state."""
    config = PlatformConfig.from_yaml(config_path)
    data_config = config.section("data")
    universe_config = config.section("universe")
    signal_config = config.section("signals")
    portfolio_config = config.section("portfolio")
    backtest_config = config.section("backtest")
    regime_config = config.section("regime")
    rolling_config = config.section("rolling")
    factor_eval_config = config.section("factor_evaluation")
    walk_config = config.section("walk_forward")

    benchmark_ticker = regime_config.get("benchmark_ticker", "SPY")
    tickers = sorted(set(get_universe(universe_config) + [benchmark_ticker]))
    if use_demo_data:
        prices = generate_demo_prices(tickers=tickers, start=data_config.get("start_date", "2018-01-01"))
    else:
        prices = download_adjusted_prices(
            tickers=tickers,
            start=data_config.get("start_date", "2018-01-01"),
            end=data_config.get("end_date"),
            auto_adjust=data_config.get("auto_adjust", True),
            cache_path=ROOT / "data" / "dashboard_prices.csv",
        )
    benchmark_prices = prices[benchmark_ticker] if benchmark_ticker in prices else None
    research_prices = prices.drop(columns=[benchmark_ticker], errors="ignore")
    factors = compute_factor_scores(research_prices, signal_config)
    research_returns = research_prices.pct_change()
    raw_factors = {
        "momentum": momentum(
            research_prices,
            lookback_days=signal_config.get("momentum_lookback_days", 252),
            skip_days=signal_config.get("momentum_skip_days", 21),
        ),
        "volatility": volatility(
            research_returns,
            lookback_days=signal_config.get("volatility_lookback_days", 63),
        ),
        "trend": trend(
            research_prices,
            window_days=signal_config.get("trend_window_days", 200),
        ),
        "mean_reversion": mean_reversion(
            research_prices,
            lookback_days=signal_config.get("mean_reversion_lookback_days", 21),
        ),
    }

    result = run_backtest(
        prices=research_prices,
        scores=factors["composite"],
        volatility=factors["volatility"],
        top_n=portfolio_config.get("top_n", 8),
        weighting=portfolio_config.get("weighting", "inverse_volatility"),
        rebalance_frequency=backtest_config.get("rebalance_frequency", "ME"),
        transaction_cost_bps=backtest_config.get("transaction_cost_bps", 10),
        slippage_bps=backtest_config.get("slippage_bps", 5),
        initial_capital=backtest_config.get("initial_capital", 100_000),
    )
    summary = performance_summary(
        result.returns,
        result.equity_curve,
        result.turnover,
        risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
    )
    rolling = rolling_metrics(
        result.returns,
        result.equity_curve,
        result.turnover,
        window=rolling_config.get("window_days", 126),
        risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
    )

    forward_return_days = factor_eval_config.get("forward_return_days", 21)
    decay_periods = factor_eval_config.get("decay_periods", [1, 5, 10, 21, 63])
    persistence_lags = factor_eval_config.get("persistence_lags", [1, 5, 21, 63])
    factor_summary, factor_details = factor_diagnostic_summary(
        factors,
        research_prices,
        forward_return_days=forward_return_days,
        decay_periods=decay_periods,
        persistence_lags=persistence_lags,
    )
    fwd = forward_returns(research_prices, forward_return_days)
    ic_frame = pd.DataFrame(
        {
            name: information_coefficient(signal, fwd)
            for name, signal in factors.items()
            if name != "composite"
        }
    )
    decay_frame = pd.DataFrame(
        {
            name: factor_decay(signal, research_prices, decay_periods)
            for name, signal in factors.items()
            if name != "composite"
        }
    ).T
    persistence_frame = pd.DataFrame(
        {
            name: signal_persistence(signal, persistence_lags)
            for name, signal in factors.items()
            if name != "composite"
        }
    ).T
    dispersion_frame = pd.DataFrame(
        {
            name: cross_sectional_dispersion(signal)
            for name, signal in factors.items()
            if name != "composite"
        }
    )
    raw_dispersion_frame = pd.DataFrame(
        {
            name: cross_sectional_dispersion(signal)
            for name, signal in raw_factors.items()
        }
    )
    monthly_raw_dispersion = raw_dispersion_frame.resample("ME").mean()
    normalized_raw_dispersion = (
        monthly_raw_dispersion - monthly_raw_dispersion.mean()
    ) / monthly_raw_dispersion.std(ddof=0)

    regimes = pd.DataFrame()
    regime_summaries = {}
    capm = pd.Series(dtype=float)
    if benchmark_prices is not None:
        regimes = classify_market_regimes(
            benchmark_prices,
            moving_average_days=regime_config.get("moving_average_days", 200),
            volatility_lookback_days=regime_config.get("volatility_lookback_days", 21),
            volatility_quantile_window=regime_config.get("volatility_quantile_window", 252),
            high_volatility_quantile=regime_config.get("high_volatility_quantile", 0.60),
        )
        regime_summaries = performance_by_regime(result.returns, result.equity_curve, result.turnover, regimes)
        capm = capm_regression(
            result.returns,
            benchmark_prices.pct_change(),
            risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
        )

    walk = run_walk_forward(
        prices=research_prices,
        factors=factors,
        volatility=factors["volatility"],
        train_months=walk_config.get("train_months", 36),
        test_months=walk_config.get("test_months", 12),
        min_train_observations=walk_config.get("min_train_observations", 252),
        top_n=portfolio_config.get("top_n", 8),
        weighting=portfolio_config.get("weighting", "inverse_volatility"),
        rebalance_frequency=backtest_config.get("rebalance_frequency", "ME"),
        transaction_cost_bps=backtest_config.get("transaction_cost_bps", 10),
        slippage_bps=backtest_config.get("slippage_bps", 5),
        initial_capital=backtest_config.get("initial_capital", 100_000),
    )

    experiment_output_dir = ROOT / config.section("experiments").get("output_dir", "reports/experiments")
    experiment_comparison = run_experiments(config.raw, research_prices, benchmark_prices, experiment_output_dir)
    latest_scores = factors["composite"].dropna(how="all").iloc[-1].sort_values(ascending=False)

    return {
        "config": config.raw,
        "use_demo_data": use_demo_data,
        "prices": prices,
        "research_prices": research_prices,
        "benchmark_prices": benchmark_prices,
        "factors": factors,
        "result": result,
        "summary": summary,
        "rolling": rolling,
        "factor_summary": factor_summary,
        "factor_details": factor_details,
        "ic_frame": ic_frame,
        "decay_frame": decay_frame,
        "persistence_frame": persistence_frame,
        "dispersion_frame": dispersion_frame,
        "raw_dispersion_frame": raw_dispersion_frame,
        "normalized_raw_dispersion": normalized_raw_dispersion,
        "regimes": regimes,
        "regime_summaries": regime_summaries,
        "capm": capm,
        "walk": walk,
        "experiment_comparison": experiment_comparison,
        "latest_scores": latest_scores,
        "reports_dir": Path(ROOT / "reports"),
    }
