from __future__ import annotations

import streamlit as st

from dashboard.bootstrap import DEFAULT_CONFIG


def render_sidebar() -> str:
    st.sidebar.title("Equity Signal Platform")
    st.sidebar.caption("Systematic equity research terminal")
    st.sidebar.page_link("app.py", label="Overview")
    st.sidebar.page_link("pages/1_Strategy_Analytics.py", label="Strategy Analytics")
    st.sidebar.page_link("pages/2_Factor_Diagnostics.py", label="Factor Diagnostics")
    st.sidebar.page_link("pages/3_Regime_Analysis.py", label="Regime Analysis")
    st.sidebar.page_link("pages/4_Experiment_Lab.py", label="Experiment Lab")
    st.sidebar.page_link("pages/5_Research_Reports.py", label="Research Reports")
    st.sidebar.divider()
    config_path = st.sidebar.text_input("Config path", str(DEFAULT_CONFIG))
    st.sidebar.divider()
    st.sidebar.markdown(
        "Use the pages above to review portfolio performance, factor quality, regimes, experiments, and reports."
    )
    st.sidebar.caption("Research/simulation only. No live trading execution.")
    return config_path


def section_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def metric_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
