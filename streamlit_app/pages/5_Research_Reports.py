from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from dashboard.bootstrap import REPORTS_DIR
from dashboard.components import render_sidebar, section_header
from dashboard.data import load_research_context


def csv_bytes(frame: pd.DataFrame | pd.Series) -> bytes:
    if isinstance(frame, pd.Series):
        frame = frame.to_frame("value")
    return frame.to_csv().encode("utf-8")


def download_frame(label: str, filename: str, frame: pd.DataFrame | pd.Series) -> None:
    st.download_button(
        label=label,
        data=csv_bytes(frame),
        file_name=filename,
        mime="text/csv",
        width="stretch",
    )


st.set_page_config(page_title="Research Reports | ESP", page_icon="ESP", layout="wide")
settings = render_sidebar()

section_header("Research Reports", "Download current research outputs and review generated artifacts.")

with st.spinner("Preparing downloadable research outputs..."):
    context = load_research_context(settings.config_path, settings.use_demo_data)

result = context["result"]
walk = context["walk"]
regime_summaries = context["regime_summaries"]

st.subheader("Current Session Downloads")
st.caption("These files are generated from the dashboard's current research context, so they are available in demo mode and on Streamlit Cloud.")

left, middle, right = st.columns(3)
with left:
    st.markdown("**Performance**")
    download_frame("Performance summary", "performance_summary.csv", context["summary"])
    download_frame(
        "Backtest returns",
        "backtest_returns.csv",
        pd.DataFrame({"strategy_return": result.returns, "equity_curve": result.equity_curve}),
    )
    download_frame("Rolling metrics", "rolling_metrics.csv", context["rolling"])
    download_frame("Walk-forward returns", "walk_forward_returns.csv", walk.returns)

with middle:
    st.markdown("**Signals And Factors**")
    download_frame("Latest signal ranks", "latest_signal_ranks.csv", context["latest_scores"])
    download_frame("Factor summary", "factor_summary.csv", context["factor_summary"])
    download_frame("Factor decay", "factor_decay.csv", context["decay_frame"])
    download_frame("Signal persistence", "signal_persistence.csv", context["persistence_frame"])

with right:
    st.markdown("**Regimes And Experiments**")
    if not context["capm"].empty:
        download_frame("CAPM regression", "capm_regression.csv", context["capm"])
    if not context["experiment_comparison"].empty:
        download_frame("Experiment comparison", "experiment_comparison.csv", context["experiment_comparison"])
    for regime_name, table in regime_summaries.items():
        download_frame(
            regime_name.replace("_", " ").title(),
            f"{regime_name}_summary.csv",
            table,
        )

st.divider()
st.subheader("Saved Report Artifacts")
st.caption("Local command-line runs may also write PNG and CSV files to the reports folder. On Streamlit Cloud this section can be empty.")

if not REPORTS_DIR.exists():
    st.info("No saved report folder found for this deployment.")
else:
    image_files = sorted(REPORTS_DIR.glob("*.png"))
    csv_files = sorted(REPORTS_DIR.glob("*.csv"))

    if image_files:
        with st.expander("Saved Charts"):
            cols = st.columns(2)
            for idx, image_path in enumerate(image_files):
                with cols[idx % 2]:
                    st.image(str(image_path), caption=image_path.name, width="stretch")

    if csv_files:
        with st.expander("Saved CSV Files"):
            for csv_path in csv_files:
                with csv_path.open("rb") as file:
                    st.download_button(
                        label=csv_path.name,
                        data=file,
                        file_name=csv_path.name,
                        mime="text/csv",
                        width="stretch",
                    )

    experiment_dir = REPORTS_DIR / "experiments"
    if experiment_dir.exists():
        artifact_files = [path for path in sorted(experiment_dir.rglob("*")) if path.is_file()]
        if artifact_files:
            with st.expander("Saved Experiment Artifacts"):
                st.dataframe(
                    [{"Artifact": str(path.relative_to(REPORTS_DIR))} for path in artifact_files],
                    width="stretch",
                    height=260,
                )

    if not image_files and not csv_files and not (REPORTS_DIR / "experiments").exists():
        st.info("No saved report artifacts found.")

