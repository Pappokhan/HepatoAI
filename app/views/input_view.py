from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from .styles import html
from .widgets import stretch

_COLS = 3  # every biomarker row uses the same 3-column grid so inputs line up


def render_single_form(specs, groups) -> Optional[Tuple[Dict[str, float], Dict[str, Optional[object]]]]:
    spec_map = {s.name: s for s in specs}
    with st.form("single_prediction_form"):
        st.markdown('<div class="form-title">Patient details <span class="opt">optional</span></div>',
                    unsafe_allow_html=True)
        c1, c2, c3 = st.columns(_COLS)
        name = c1.text_input("Patient name", placeholder="Name")
        patient_id = c2.text_input("Patient ID", placeholder="ID")
        age = c3.number_input("Age (years)", min_value=0, max_value=120, value=None, step=1)

        st.markdown('<div class="form-title mt">Biomarker values</div>', unsafe_allow_html=True)
        values: Dict[str, float] = {}
        for title, names in groups:
            st.markdown(f'<div class="group-title">{title}</div>', unsafe_allow_html=True)
            cols = st.columns(_COLS)
            for col, n in zip(cols, names):
                s = spec_map[n]
                with col:
                    values[n] = st.number_input(
                        s.input_label, min_value=float(s.min_value), max_value=float(s.max_value),
                        value=float(s.default), step=float(s.step), format=s.fmt,
                        help=s.help, key=f"in_{n}")
        submitted = st.form_submit_button("Analyze", type="primary", **stretch(st.form_submit_button))
    if not submitted:
        return None
    ordered = {s.name: values[s.name] for s in specs}
    patient = {"name": name.strip(), "patient_id": patient_id.strip(),
               "age": int(age) if age else None}
    return ordered, patient


def render_model_note(summary: dict):
    acc = summary.get("accuracy")
    acc_txt = f"{acc:.2%}" if acc is not None else "n/a"
    st.markdown(html(f"""
    <div class="model-note"><div class="mn-title">About the model</div>
    <div class="mn-grid"><span>Algorithm</span><b>{summary["name"]}</b>
    <span>Inputs</span><b>{summary["n_features"]} routine blood markers</b>
    <span>Development accuracy</span><b>{acc_txt}</b></div>
    <p>Accuracy was measured on the development dataset only. The model has not been validated on
    independent patients, so read the result alongside the reference ranges.</p></div>"""),
                unsafe_allow_html=True)


def render_batch_upload(template_csv: str, feature_names: List[str]) -> Optional[pd.DataFrame]:
    st.markdown("##### Batch prediction")
    st.write("Upload a CSV with these exact columns:")
    st.code(", ".join(feature_names), language="text")
    st.download_button("Download CSV template", template_csv,
                       file_name="hepatoai_template.csv", mime="text/csv")
    file = st.file_uploader("CSV file", type=["csv"])
    if file is None:
        return None
    try:
        return pd.read_csv(file)
    except Exception as e:
        st.error(f"Could not read the CSV: {e}")
        return None
