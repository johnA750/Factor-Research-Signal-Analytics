from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard.bootstrap import REPORTS_DIR
from dashboard.components import render_sidebar, section_header


st.set_page_config(page_title="Research Reports | ESP", page_icon="ESP", layout="wide")
render_sidebar()

section_header("Research Reports", "Generated charts, CSV outputs, and experiment artifacts.")

if not REPORTS_DIR.exists():
    st.info("No reports directory exists yet. Run a backtest or experiment first.")
else:
    image_files = sorted(REPORTS_DIR.glob("*.png"))
    csv_files = sorted(REPORTS_DIR.glob("*.csv"))

    st.subheader("Generated Charts")
    if image_files:
        cols = st.columns(2)
        for idx, image_path in enumerate(image_files):
            with cols[idx % 2]:
                st.image(str(image_path), caption=image_path.name, use_container_width=True)
    else:
        st.info("No chart images found in reports.")

    st.subheader("Downloadable CSV Outputs")
    for csv_path in csv_files:
        with csv_path.open("rb") as file:
            st.download_button(
                label=f"Download {csv_path.name}",
                data=file,
                file_name=csv_path.name,
                mime="text/csv",
            )

    st.subheader("Experiment Artifacts")
    experiment_dir = REPORTS_DIR / "experiments"
    if experiment_dir.exists():
        for path in sorted(experiment_dir.rglob("*")):
            if path.is_file():
                st.caption(str(path.relative_to(REPORTS_DIR)))
    else:
        st.info("No experiment artifacts found.")
