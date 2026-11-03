import html as _h

import pandas as pd
import streamlit as st

from app import config
from app.models import PredictionResult
from .styles import html
from .widgets import stretch

_BADGE = {"LOW": "warn", "HIGH": "bad", "NORMAL": "ok", "UNKNOWN": "muted"}


def _marker_row(r: dict) -> str:
    cls = _BADGE[r["status"]]
    lo, hi = r["range"]
    rng = "-" if lo is None else f"{lo:g} - {hi:g}"
    track = ""
    if r["pos"] is not None:
        track = (f'<div class="track"><div class="zone" style="left:{r["zone_start"]*100:.1f}%;'
                 f'width:{r["zone_width"]*100:.1f}%"></div>'
                 f'<div class="dot {cls}" style="left:{min(max(r["pos"],0),1)*100:.1f}%"></div></div>')
    row_cls = {"bad": "row-bad", "warn": "row-warn"}.get(cls, "")
    return (f'<tr class="{row_cls}"><td class="mk-name">{_h.escape(r["marker"])}</td>'
            f'<td class="mk-val">{r["value"]:g} <span class="unit">{_h.escape(r["unit"])}</span></td>'
            f'<td class="mk-rng">{rng}</td><td>{track}</td>'
            f'<td><span class="badge {cls}">{r["status"].title()}</span></td></tr>')


def render_empty_state():
    st.markdown('<div class="empty"><b>No analysis yet</b><br>Enter the biomarker values on the left and '
                'click <b>Analyze</b> to see the risk assessment and download the PDF report.</div>',
                unsafe_allow_html=True)


def render_single_result(res: PredictionResult, analysis: dict, report_pdf: bytes, report_name: str):
    band_label, band_cls = analysis["band"]
    card_cls = "bad" if res.is_positive else "ok"
    st.markdown(html(f"""
    <div class="result-card {card_cls}">
      <div class="rc-main">
        <div class="rc-kicker">Screening result</div>
        <div class="rc-title">{_h.escape(res.label_text)}</div>
        <div class="rc-sub">Risk band <span class="pill {band_cls}">{band_label}</span></div>
      </div>
      <div class="rc-side">
        <div class="rc-prob">{res.probability_positive:.1%}</div>
        <div class="rc-probl">probability of liver disease</div>
      </div>
    </div>
    <div class="meter"><div class="meter-fill {card_cls}" style="width:{res.probability_positive*100:.1f}%"></div>
    <div class="meter-mid"></div></div>
    <div class="meter-scale"><span>0%</span><span>50% decision threshold</span><span>100%</span></div>"""),
                unsafe_allow_html=True)

    notice = analysis.get("notice")
    if notice:
        st.markdown(html(f'<div class="notice"><b>{_h.escape(notice["title"])}</b>'
                         f'<p>{_h.escape(notice["text"])}</p></div>'), unsafe_allow_html=True)

    st.download_button("Download PDF report", report_pdf, file_name=report_name,
                       mime="application/pdf", type="primary", key="dl_report", **stretch(st.download_button))

    st.markdown('<div class="section-title">Biomarker review</div>', unsafe_allow_html=True)
    rows = "".join(_marker_row(r) for r in analysis["flags"])
    st.markdown(html(f"""
    <div class="mk-wrap"><table class="mk-table">
    <colgroup><col style="width:27%"><col style="width:14%"><col style="width:18%"><col style="width:27%"><col style="width:14%"></colgroup>
    <thead><tr><th>Biomarker</th><th>Result</th><th>Typical range</th><th>Position vs. range</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
    <div class="table-note">Green zone = typical adult range; dot = entered value. Ranges vary by laboratory.</div>"""),
                unsafe_allow_html=True)

    items = "".join(f"<li>{_h.escape(f)}</li>" for f in analysis["findings"])
    st.markdown(html(f'<div class="callout"><b>Key findings</b><ul>{items}</ul></div>'),
                unsafe_allow_html=True)

    with st.expander("Class probabilities"):
        st.bar_chart(pd.Series(res.probabilities, name="probability"), height=160)


def render_batch_result(df: pd.DataFrame):
    st.subheader("Batch results")
    n_pos = int((df["Prediction"] == config.POSITIVE_TEXT).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(df))
    c2.metric("Flagged as disease", n_pos)
    c3.metric("Not flagged", len(df) - n_pos)
    st.dataframe(df)
    st.download_button("Download predictions (CSV)", df.to_csv(index=False),
                       file_name="hepatoai_predictions.csv", mime="text/csv")
