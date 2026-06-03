from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard import charts
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context


st.set_page_config(page_title="Factor Diagnostics | FRSA", page_icon="FRSA", layout="wide")
settings = render_sidebar()

section_header("Factor Diagnostics", "Cross-sectional signal quality, decay, persistence, and dispersion.")

with st.spinner("Loading factor diagnostics..."):
    context = load_research_context(settings.config_path, settings.use_demo_data)

factor_summary = context["factor_summary"]

st.caption("IC is the Spearman rank correlation between factor scores and forward returns. Hit rate measures how often top-ranked names beat bottom-ranked names.")
st.dataframe(factor_summary, use_container_width=True, height=210)

left, right = st.columns(2)
with left:
    st.plotly_chart(charts.factor_ic_chart(context["ic_frame"]), use_container_width=True)
with right:
    st.plotly_chart(charts.bar_chart(factor_summary, ["mean_ic", "hit_rate"], "Factor Quality"), use_container_width=True)

left, right = st.columns(2)
with left:
    st.caption("Factor decay shows how average IC changes as the forward-return horizon increases.")
    st.plotly_chart(charts.factor_decay_chart(context["decay_frame"]), use_container_width=True)
with right:
    st.caption("Persistence measures rank stability across lags; high values imply slower-changing signals.")
    st.dataframe(context["persistence_frame"], use_container_width=True, height=360)

st.subheader("Dispersion Analysis")
st.caption("Monthly normalized dispersion of raw factor values. Higher values mean stronger cross-sectional separation.")
st.plotly_chart(
    charts.line_chart(
        context["normalized_raw_dispersion"],
        list(context["normalized_raw_dispersion"].columns),
        "Normalized Cross-Sectional Dispersion",
        420,
    ),
    use_container_width=True,
)

st.subheader("Current Composite Rankings")
st.dataframe(context["latest_scores"].head(20).rename("Composite Score").to_frame(), use_container_width=True)
