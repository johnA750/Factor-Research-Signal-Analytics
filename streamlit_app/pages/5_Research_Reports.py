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

    st.subheader("Downloadable Outputs")
    if not csv_files:
        st.info("No CSV outputs found.")
    else:
        groups = {
            "Performance": ["performance", "backtest", "rolling", "walk_forward"],
            "Signals And Factors": ["signal", "factor"],
            "Regimes And Regression": ["regime", "capm"],
        }
        used_files = set()
        for group_name, keywords in groups.items():
            grouped = [path for path in csv_files if any(keyword in path.name for keyword in keywords)]
            used_files.update(grouped)
            if grouped:
                with st.expander(group_name, expanded=group_name == "Performance"):
                    for csv_path in grouped:
                        with csv_path.open("rb") as file:
                            st.download_button(
                                label=csv_path.name,
                                data=file,
                                file_name=csv_path.name,
                                mime="text/csv",
                                use_container_width=True,
                            )
        remaining = [path for path in csv_files if path not in used_files]
        if remaining:
            with st.expander("Other Outputs"):
                for csv_path in remaining:
                    with csv_path.open("rb") as file:
                        st.download_button(
                            label=csv_path.name,
                            data=file,
                            file_name=csv_path.name,
                            mime="text/csv",
                            use_container_width=True,
                        )

    st.subheader("Experiment Artifacts")
    experiment_dir = REPORTS_DIR / "experiments"
    if experiment_dir.exists():
        artifact_files = [path for path in sorted(experiment_dir.rglob("*")) if path.is_file()]
        if artifact_files:
            st.dataframe(
                [{"Artifact": str(path.relative_to(REPORTS_DIR))} for path in artifact_files],
                use_container_width=True,
                height=260,
            )
        else:
            st.info("No experiment artifact files found.")
    else:
        st.info("No experiment artifacts found.")
