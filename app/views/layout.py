import streamlit as st

from app import config
from . import styles


def setup_page():
    st.set_page_config(page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide",
                       initial_sidebar_state="collapsed")
    styles.inject()


def render_header():
    st.markdown(styles.html(f"""
    <div class="hero">
      <div class="hero-l"><span class="hero-ico"><i></i></span>
        <div><h1>{config.APP_TITLE}</h1><p>{config.APP_SUBTITLE}</p></div></div>
      <div class="hero-r"><span class="chip">Explainable screening</span><span class="chip">PDF report</span>
      <span class="chip">AI assistant</span></div>
    </div>"""), unsafe_allow_html=True)


def render_sidebar(summary: dict):
    with st.sidebar:
        st.markdown(f"### {config.APP_ICON} {config.APP_TITLE}")
        st.caption("Routine liver-panel blood tests in, risk analysis out.")
        st.markdown("**How to use**")
        st.markdown("1. Enter biomarkers in **Single patient**\n"
                    "2. Review the risk analysis\n"
                    "3. Download the **PDF report**\n"
                    "4. Ask the **AI assistant** to explain it")
        st.divider()
        st.markdown("**Model**")
        st.write(summary["name"])
        acc = summary.get("accuracy")
        if acc is not None:
            st.caption(f"Reported development accuracy: {acc:.2%}")
        st.divider()
        st.warning(config.DISCLAIMER)


def render_footer():
    st.markdown(f'<div class="app-footer">{config.APP_TITLE} &middot; research and educational use only'
                f' &middot; not a medical diagnosis</div>', unsafe_allow_html=True)
