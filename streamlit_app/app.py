from __future__ import annotations

import streamlit as st

from dashboard import charts
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context
from dashboard.formatting import format_number, format_percent


st.set_page_config(
    page_title="Equity Signal Platform",
    page_icon="ESP",
    layout="wide",
    initial_sidebar_state="expanded",
)

settings = render_sidebar()

section_header(
    "Overview",
    "A compact dashboard for systematic equity factor research, simulation backtests, and experiment comparison.",
)

with st.spinner("Loading research context..."):
    context = load_research_context(settings.config_path, settings.use_demo_data)

summary = context["summary"]
experiment_comparison = context["experiment_comparison"]

st.markdown(
    "Systematic equity research studies rules-based signals across a stock universe. "
    "This demo shows a simulated long-only factor strategy, diagnostics for the underlying signals, "
    "and comparisons across simple experiment settings."
)

metric_cols = st.columns(3)
metric_cols[0].metric("Total Return", format_percent(summary["total_return"]))
metric_cols[1].metric("CAGR", format_percent(summary["annualized_return"]))
metric_cols[2].metric("Sharpe", format_number(summary["sharpe_ratio"]), help="Risk-adjusted return: average excess return divided by volatility.")

metric_cols = st.columns(3)
metric_cols[0].metric("Volatility", format_percent(summary["annualized_volatility"]))
metric_cols[1].metric("Max DD", format_percent(summary["max_drawdown"]), help="Largest peak-to-trough portfolio decline in the simulation.")
metric_cols[2].metric("Avg Turnover", format_percent(summary["average_rebalance_turnover"]))

left, right = st.columns([2, 1])

with left:
    st.plotly_chart(charts.equity_curve(context), use_container_width=True)
    st.plotly_chart(charts.drawdown(context["result"].equity_curve), use_container_width=True)

with right:
    st.subheader("Current Top Signals")
    st.dataframe(
        context["latest_scores"].head(12).rename("Composite Score").to_frame(),
        use_container_width=True,
        height=360,
    )

    st.subheader("Latest Experiments")
    if experiment_comparison.empty:
        st.info("No experiment comparison is available yet.")
    else:
        display_cols = ["annualized_return", "sharpe_ratio", "max_drawdown"]
        experiment_display = experiment_comparison[display_cols].sort_values("sharpe_ratio", ascending=False).copy()
        experiment_display["annualized_return"] *= 100.0
        experiment_display["max_drawdown"] *= 100.0
        st.dataframe(
            experiment_display,
            use_container_width=True,
            height=240,
            column_config={
                "annualized_return": st.column_config.NumberColumn("CAGR", format="%.1f%%"),
                "sharpe_ratio": st.column_config.NumberColumn("Sharpe", format="%.2f"),
                "max_drawdown": st.column_config.NumberColumn("Max DD", format="%.1f%%"),
            },
        )

st.subheader("Research Snapshot")
snapshot_cols = st.columns(4)
snapshot_cols[0].metric("Universe Size", len(context["research_prices"].columns))
snapshot_cols[1].metric("Observations", f"{len(context['result'].returns):,}")
snapshot_cols[2].metric("Walk-Forward Windows", len(context["walk"].windows))
snapshot_cols[3].metric("Avg. Turnover", format_percent(summary["average_rebalance_turnover"]))
