from typing import Dict, List, Optional, Tuple

import streamlit as st

from app import config
from .styles import html
from .widgets import stretch


def render_settings(env_provider: Optional[str], env_ready: bool) -> Tuple[Optional[str], Optional[str]]:
    if env_ready:
        st.caption(f"AI provider: **{env_provider}** (API key loaded)")
        return None, None
    with st.expander("AI settings (API key required)", expanded=False):
        provider = st.selectbox("Provider", ["gemini", "groq"])
        key = st.text_input(f"{provider.title()} API key", type="password",
                            help="Kept only in this browser session. To save it permanently, paste it "
                                 "into local_settings.py.")
    return provider, (key or None)


def render_test_button() -> bool:
    return st.button("Test connection", key="test_ai", **stretch(st.button))


def render_test_result(ok: bool, message: str):
    (st.success if ok else st.error)(message)


def render_context_banner(has_context: bool):
    if has_context:
        st.markdown('<div class="ctx ok"><span></span>Latest prediction loaded: answers will use your result</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="ctx"><span></span>No prediction yet: run one in Single patient for '
                    'personalised answers</div>', unsafe_allow_html=True)


def render_welcome(has_context: bool) -> Optional[str]:
    """ChatGPT-style empty state: greeting plus suggestion cards. Returns the clicked suggestion."""
    sub = ("Ask about your latest result, a marker, or what to discuss with your doctor."
           if has_context else "Ask a general question about liver markers, or run an analysis first.")
    st.markdown(html(f"""
    <div class="chat-welcome"><div class="cw-badge"><i></i></div>
    <h3>How can I help with your results?</h3><p>{sub}</p></div>"""), unsafe_allow_html=True)
    clicked = None
    cols = st.columns(len(config.QUICK_PROMPTS))
    for i, q in enumerate(config.QUICK_PROMPTS):
        with cols[i]:
            if st.button(q, key=f"qp_{i}", **stretch(st.button)):
                clicked = q
    return clicked


def render_history(messages: List[Dict[str, str]]):
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])


def render_input() -> Optional[str]:
    return st.chat_input("Message HepatoAI...")


def render_clear_button() -> bool:
    return st.button("New chat", key="clear_chat", **stretch(st.button))
