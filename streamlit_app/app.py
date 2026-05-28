from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from equity_signal_platform.analytics import (
    capm_regression,
    classify_market_regimes,
    factor_diagnostic_summary,
    performance_by_regime,
    performance_summary,
    rolling_metrics,
)
from equity_signal_platform.backtesting import run_backtest, run_walk_forward
from equity_signal_platform.config import PlatformConfig
from equity_signal_platform.data import download_adjusted_prices
from equity_signal_platform.experiments import run_experiments
from equity_signal_platform.signals import compute_factor_scores
from equity_signal_platform.universe import get_universe
import pandas as pd


@st.cache_data(show_spinner=False)
def load_backtest(config_path: str):
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
    prices = download_adjusted_prices(
        tickers=sorted(set(get_universe(universe_config) + [benchmark_ticker])),
        start=data_config.get("start_date", "2018-01-01"),
        end=data_config.get("end_date"),
        auto_adjust=data_config.get("auto_adjust", True),
        cache_path=ROOT / "data" / "dashboard_prices.csv",
    )
    benchmark_prices = prices[benchmark_ticker] if benchmark_ticker in prices else None
    research_prices = prices.drop(columns=[benchmark_ticker], errors="ignore")
    factors = compute_factor_scores(research_prices, signal_config)
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
    factor_summary, _ = factor_diagnostic_summary(
        factors,
        research_prices,
        forward_return_days=factor_eval_config.get("forward_return_days", 21),
        decay_periods=factor_eval_config.get("decay_periods", [1, 5, 10, 21, 63]),
        persistence_lags=factor_eval_config.get("persistence_lags", [1, 5, 21, 63]),
    )
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
    experiment_comparison = run_experiments(
        config.raw,
        research_prices,
        benchmark_prices,
        output_dir=ROOT / config.section("experiments").get("output_dir", "reports/experiments"),
    )
    latest_scores = factors["composite"].dropna(how="all").iloc[-1].sort_values(ascending=False)
    return result, summary, latest_scores, rolling, factor_summary, regime_summaries, capm, walk, experiment_comparison


def percent(value: float) -> str:
    return f"{value:.2%}" if pd.notna(value) else "n/a"


st.set_page_config(page_title="Equity Signal Platform", layout="wide")
st.title("Equity Signal Platform")

config_path = st.sidebar.text_input("Config path", str(ROOT / "config" / "default.yaml"))

with st.spinner("Running research backtest..."):
    result, summary, latest_scores, rolling, factor_summary, regime_summaries, capm, walk, experiment_comparison = load_backtest(config_path)

strategy_tab, regime_tab, factor_tab, experiment_tab = st.tabs(
    ["Strategy Analytics", "Regime Analysis", "Factor Diagnostics", "Experiment Comparison"]
)

with strategy_tab:
    metric_cols = st.columns(5)
    metric_cols[0].metric("Total Return", percent(summary["total_return"]))
    metric_cols[1].metric("Ann. Return", percent(summary["annualized_return"]))
    metric_cols[2].metric("Ann. Volatility", percent(summary["annualized_volatility"]))
    metric_cols[3].metric("Sharpe", f"{summary['sharpe_ratio']:.2f}")
    metric_cols[4].metric("Max Drawdown", percent(summary["max_drawdown"]))

    equity_fig = go.Figure()
    equity_fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve.values,
            mode="lines",
            name="In-Sample Backtest",
        )
    )
    if not walk.equity_curve.empty:
        equity_fig.add_trace(
            go.Scatter(
                x=walk.equity_curve.index,
                y=walk.equity_curve.values,
                mode="lines",
                name="Walk-Forward OOS",
            )
        )
    equity_fig.update_layout(
        title="Equity Curve",
        xaxis_title="Date",
        yaxis_title="Portfolio Value",
        template="plotly_white",
        height=420,
    )
    st.plotly_chart(equity_fig, use_container_width=True)

    rolling_fig = go.Figure()
    for column in ["rolling_sharpe", "rolling_volatility", "rolling_drawdown", "rolling_turnover"]:
        rolling_fig.add_trace(go.Scatter(x=rolling.index, y=rolling[column], mode="lines", name=column))
    rolling_fig.update_layout(title="Rolling Analytics", template="plotly_white", height=420)
    st.plotly_chart(rolling_fig, use_container_width=True)

    if not capm.empty:
        st.dataframe(capm.rename("value").to_frame(), use_container_width=True)

with regime_tab:
    for name, table in regime_summaries.items():
        st.subheader(name.replace("_", " ").title())
        st.dataframe(table, use_container_width=True)
        if not table.empty and "annualized_return" in table:
            fig = go.Figure(go.Bar(x=table.index, y=table["annualized_return"], name="Annualized Return"))
            fig.update_layout(template="plotly_white", height=320)
            st.plotly_chart(fig, use_container_width=True)

with factor_tab:
    st.dataframe(factor_summary, use_container_width=True)
    factor_fig = go.Figure()
    for metric in ["mean_ic", "hit_rate", "average_dispersion"]:
        factor_fig.add_trace(go.Bar(x=factor_summary.index, y=factor_summary[metric], name=metric))
    factor_fig.update_layout(barmode="group", title="Factor Diagnostics", template="plotly_white", height=380)
    st.plotly_chart(factor_fig, use_container_width=True)

    st.subheader("Current Top-Ranked Signals")
    st.dataframe(
        latest_scores.head(15).rename("Composite Score").to_frame(),
        use_container_width=True,
    )

with experiment_tab:
    st.dataframe(experiment_comparison, use_container_width=True)
    if not experiment_comparison.empty:
        comparison_fig = go.Figure()
        for metric in ["annualized_return", "sharpe_ratio", "max_drawdown"]:
            comparison_fig.add_trace(
                go.Bar(x=experiment_comparison.index, y=experiment_comparison[metric], name=metric)
            )
        comparison_fig.update_layout(
            barmode="group",
            title="Experiment Comparison",
            template="plotly_white",
            height=380,
        )
        st.plotly_chart(comparison_fig, use_container_width=True)

    st.subheader("Walk-Forward Windows")
    st.dataframe(walk.windows, use_container_width=True)
    st.subheader("Walk-Forward Factor Weights")
    st.dataframe(walk.factor_weights, use_container_width=True)
