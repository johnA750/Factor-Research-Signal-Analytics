from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from dashboard import charts
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context


st.set_page_config(page_title="Experiment Lab | ESP", page_icon="ESP", layout="wide")
settings = render_sidebar()

section_header("Experiment Lab", "Compare config-driven strategy variants and inspect saved experiment metadata.")

with st.spinner("Loading experiment results..."):
    context = load_research_context(settings.config_path, settings.use_demo_data)

comparison = context["experiment_comparison"]
if comparison.empty:
    st.info("No experiments are configured.")
else:
    sort_col = st.selectbox("Sort experiments by", comparison.columns.tolist(), index=comparison.columns.get_loc("sharpe_ratio"))
    st.dataframe(comparison.sort_values(sort_col, ascending=False), use_container_width=True)
    st.plotly_chart(
        charts.bar_chart(
            comparison,
            ["annualized_return", "sharpe_ratio", "max_drawdown"],
            "Experiment Comparison",
            420,
        ),
        use_container_width=True,
    )

    st.subheader("Parameter Comparison")
    definitions = context["config"].get("experiments", {}).get("definitions", [])
    params = pd.json_normalize(definitions).set_index("name") if definitions else pd.DataFrame()
    st.dataframe(params, use_container_width=True)

    st.subheader("Experiment Metadata")
    experiment_dir = Path(context["config"].get("experiments", {}).get("output_dir", "reports/experiments"))
    for experiment_name in comparison.index:
        metadata_path = Path(context["reports_dir"]).parent / experiment_dir / experiment_name / "metadata.json"
        if metadata_path.exists():
            with st.expander(experiment_name):
                st.json(json.loads(metadata_path.read_text(encoding="utf-8")))

    st.subheader("Walk-Forward Windows")
    st.dataframe(context["walk"].windows, use_container_width=True)

    st.subheader("Walk-Forward Factor Weights")
    st.dataframe(context["walk"].factor_weights, use_container_width=True)
