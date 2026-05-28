from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard import charts
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context


st.set_page_config(page_title="Regime Analysis | ESP", page_icon="ESP", layout="wide")
settings = render_sidebar()

section_header("Regime Analysis", "Performance across bull, bear, high-volatility, and low-volatility market states.")

with st.spinner("Loading regime analysis..."):
    context = load_research_context(settings.config_path, settings.use_demo_data)

regime_summaries = context["regime_summaries"]
if not regime_summaries:
    st.info("Regime summaries are unavailable because benchmark data was not loaded.")
else:
    for name, table in regime_summaries.items():
        st.subheader(name.replace("_", " ").title())
        left, right = st.columns([1.1, 1])
        with left:
            st.dataframe(table, use_container_width=True)
        with right:
            st.plotly_chart(
                charts.bar_chart(
                    table,
                    ["annualized_return", "sharpe_ratio", "max_drawdown"],
                    f"{name.replace('_', ' ').title()} Metrics",
                    330,
                ),
                use_container_width=True,
            )
