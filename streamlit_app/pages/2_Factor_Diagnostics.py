from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard import charts
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context


st.set_page_config(page_title="Factor Diagnostics | ESP", page_icon="ESP", layout="wide")
config_path = render_sidebar()

section_header("Factor Diagnostics", "Cross-sectional signal quality, decay, persistence, and dispersion.")

with st.spinner("Loading factor diagnostics..."):
    context = load_research_context(config_path)

factor_summary = context["factor_summary"]

st.dataframe(factor_summary, use_container_width=True)

left, right = st.columns(2)
with left:
    st.plotly_chart(charts.factor_ic_chart(context["ic_frame"]), use_container_width=True)
with right:
    st.plotly_chart(charts.bar_chart(factor_summary, ["mean_ic", "hit_rate"], "Factor Quality"), use_container_width=True)

left, right = st.columns(2)
with left:
    st.plotly_chart(charts.factor_decay_chart(context["decay_frame"]), use_container_width=True)
with right:
    st.dataframe(context["persistence_frame"], use_container_width=True)

st.plotly_chart(
    charts.line_chart(
        context["dispersion_frame"],
        list(context["dispersion_frame"].columns),
        "Cross-Sectional Dispersion",
        420,
    ),
    use_container_width=True,
)

st.subheader("Current Composite Rankings")
st.dataframe(context["latest_scores"].head(20).rename("Composite Score").to_frame(), use_container_width=True)
