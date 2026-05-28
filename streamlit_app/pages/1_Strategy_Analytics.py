from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard import charts
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context
from dashboard.formatting import format_number, format_percent


st.set_page_config(page_title="Strategy Analytics | ESP", page_icon="ESP", layout="wide")
settings = render_sidebar()

section_header("Strategy Analytics", "Rolling performance diagnostics, turnover, returns, and CAPM exposure.")

with st.spinner("Loading strategy analytics..."):
    context = load_research_context(settings.config_path, settings.use_demo_data)

result = context["result"]
rolling = context["rolling"]
summary = context["summary"]

cols = st.columns(5)
cols[0].metric("CAGR", format_percent(summary["annualized_return"]))
cols[1].metric("Volatility", format_percent(summary["annualized_volatility"]))
cols[2].metric("Sharpe", f"{summary['sharpe_ratio']:.2f}")
cols[3].metric("Max Drawdown", format_percent(summary["max_drawdown"]))
cols[4].metric("Turnover", format_percent(summary["average_rebalance_turnover"]))

st.plotly_chart(
    charts.line_chart(
        rolling,
        ["rolling_sharpe", "rolling_volatility", "rolling_drawdown", "rolling_turnover"],
        "Rolling Strategy Metrics",
        460,
    ),
    use_container_width=True,
)

left, right = st.columns(2)
with left:
    rolling_returns = result.returns.rolling(63).apply(lambda values: (1.0 + values).prod() - 1.0)
    st.plotly_chart(
        charts.line_chart(
            rolling.assign(rolling_63d_return=rolling_returns),
            ["rolling_63d_return"],
            "Rolling 63-Day Return",
            340,
        ),
        use_container_width=True,
    )

with right:
    st.plotly_chart(charts.monthly_return_heatmap(result.returns), use_container_width=True)

st.subheader("CAPM Regression")
if context["capm"].empty:
    st.info("CAPM results are unavailable because benchmark data was not loaded.")
else:
    capm_cols = st.columns(3)
    capm_cols[0].metric("Annualized Alpha", format_percent(context["capm"]["annualized_alpha"]))
    capm_cols[1].metric("Market Beta", format_number(context["capm"]["beta"]))
    capm_cols[2].metric("R-Squared", format_percent(context["capm"]["r_squared"]))
    st.dataframe(context["capm"].rename("value").to_frame(), use_container_width=True)
