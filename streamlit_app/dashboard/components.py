from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from dashboard.bootstrap import DEFAULT_CONFIG


@dataclass(frozen=True)
class DashboardSettings:
    config_path: str
    use_demo_data: bool


def render_sidebar() -> DashboardSettings:
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
    use_demo_data = st.sidebar.toggle(
        "Use fast demo data",
        value=True,
        help="Use deterministic synthetic prices for quick demos. Turn off to download Yahoo Finance data.",
    )
    if st.sidebar.button("Refresh Research Data"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.divider()
    st.sidebar.markdown(
        "Use the pages above to review portfolio performance, factor quality, regimes, experiments, and reports."
    )
    st.sidebar.caption("Research/simulation only. No live trading execution.")
    return DashboardSettings(config_path=config_path, use_demo_data=use_demo_data)


def section_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def metric_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
