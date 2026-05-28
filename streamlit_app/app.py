from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from equity_signal_platform.analytics import performance_summary
from equity_signal_platform.backtesting import run_backtest
from equity_signal_platform.config import PlatformConfig
from equity_signal_platform.data import download_adjusted_prices
from equity_signal_platform.signals import compute_factor_scores
from equity_signal_platform.universe import get_universe


@st.cache_data(show_spinner=False)
def load_backtest(config_path: str):
    config = PlatformConfig.from_yaml(config_path)
    data_config = config.section("data")
    universe_config = config.section("universe")
    signal_config = config.section("signals")
    portfolio_config = config.section("portfolio")
    backtest_config = config.section("backtest")

    prices = download_adjusted_prices(
        tickers=get_universe(universe_config),
        start=data_config.get("start_date", "2018-01-01"),
        end=data_config.get("end_date"),
        auto_adjust=data_config.get("auto_adjust", True),
        cache_path=ROOT / "data" / "dashboard_prices.csv",
    )
    factors = compute_factor_scores(prices, signal_config)
    result = run_backtest(
        prices=prices,
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
    latest_scores = factors["composite"].dropna(how="all").iloc[-1].sort_values(ascending=False)
    return result, summary, latest_scores


def percent(value: float) -> str:
    return f"{value:.2%}" if pd.notna(value) else "n/a"


st.set_page_config(page_title="Equity Signal Platform", layout="wide")
st.title("Equity Signal Platform")

config_path = st.sidebar.text_input("Config path", str(ROOT / "config" / "default.yaml"))

with st.spinner("Running research backtest..."):
    result, summary, latest_scores = load_backtest(config_path)

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
        name="Equity Curve",
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

drawdown = result.equity_curve / result.equity_curve.cummax() - 1.0
drawdown_fig = go.Figure()
drawdown_fig.add_trace(
    go.Scatter(
        x=drawdown.index,
        y=drawdown.values,
        fill="tozeroy",
        mode="lines",
        name="Drawdown",
    )
)
drawdown_fig.update_layout(
    title="Drawdown",
    xaxis_title="Date",
    yaxis_title="Drawdown",
    template="plotly_white",
    height=320,
)
st.plotly_chart(drawdown_fig, use_container_width=True)

st.subheader("Current Top-Ranked Signals")
st.dataframe(
    latest_scores.head(15).rename("Composite Score").to_frame(),
    use_container_width=True,
)

