import os
import warnings

os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 4))
warnings.filterwarnings("ignore", message=".*force_all_finite.*", category=FutureWarning)
warnings.filterwarnings("ignore", message="Could not find the number of physical cores.*", category=UserWarning)

try:
    from joblib.externals.loky.backend import context as _loky_context
    _loky_context.physical_cores_cache = os.cpu_count() or 4
except Exception:
    pass

import streamlit as st

from app.controllers import AgentController, PredictionController
from app.models import LLMError
from app.views import agent_view, input_view, layout, result_view


@st.cache_resource(show_spinner="Loading model...")
def get_controller() -> PredictionController:
    return PredictionController()


def render_assistant_tab(ctrl: PredictionController):
    agent = AgentController(ctrl.feature_specs)
    context = st.session_state.get("last_prediction")
    messages = st.session_state.setdefault("chat", [])

    _, mid, _ = st.columns([1, 5, 1])
    with mid:
        env_provider = agent.default_provider()
        env_ready = agent.provider_ready()
        provider, api_key = agent_view.render_settings(env_provider, env_ready)

        top = st.columns([6, 1.5, 1.3], vertical_alignment="center")
        with top[0]:
            agent_view.render_context_banner(context is not None)
        with top[1]:
            test_clicked = agent_view.render_test_button()
        with top[2]:
            clear_clicked = bool(messages) and agent_view.render_clear_button()
        if test_clicked:
            with st.spinner("Testing connection..."):
                ok, msg = agent.test_connection(provider, api_key)
            agent_view.render_test_result(ok, msg)
        if clear_clicked:
            st.session_state["chat"] = []
            st.rerun()

        chat_box = st.container(height=470, border=False)
        clicked = None
        welcome = None
        with chat_box:
            if messages:
                agent_view.render_history(messages)
            else:
                welcome = st.empty()
                with welcome.container():
                    clicked = agent_view.render_welcome(context is not None)
        prompt = agent_view.render_input() or clicked

        if prompt:
            messages.append({"role": "user", "content": prompt})
            with chat_box:
                if welcome is not None:
                    welcome.empty()  # drop the welcome screen once the conversation starts
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            reply = agent.ask(messages, context, provider, api_key)
                        except LLMError as e:
                            reply = f"\u26a0\ufe0f {e}"
                    st.markdown(reply)
            messages.append({"role": "assistant", "content": reply})


def report_for(ctrl: PredictionController, pred: dict, analysis: dict) -> bytes:
    """Build the PDF once per prediction, not on every Streamlit rerun (chat messages, tab clicks...)."""
    cached = st.session_state.get("report_cache")
    if cached and cached[0] == pred["report_id"]:
        return cached[1]
    pdf = ctrl.build_report(pred, analysis)
    st.session_state["report_cache"] = (pred["report_id"], pdf)
    return pdf


def render_single_tab(ctrl: PredictionController):
    left, right = st.columns([5, 6], gap="large")
    with left:
        submitted = input_view.render_single_form(ctrl.feature_specs, ctrl.feature_groups)
        if submitted is not None:
            values, patient = submitted
            st.session_state["last_prediction"] = ctrl.run_prediction(values, patient)
        input_view.render_model_note(ctrl.model_summary())
    with right:
        pred = st.session_state.get("last_prediction")
        if pred:
            analysis = ctrl.analyze(pred)
            result_view.render_single_result(pred["result"], analysis, report_for(ctrl, pred, analysis),
                                             ctrl.report_filename(pred))
        else:
            result_view.render_empty_state()


def main():
    layout.setup_page()
    layout.render_header()

    try:
        ctrl = get_controller()
    except Exception as e:
        st.error(f"Failed to load model artifacts: {e}")
        st.stop()

    tab_single, tab_ai = st.tabs(["Single patient", "AI assistant"])
    with tab_single:
        render_single_tab(ctrl)
    with tab_ai:
        render_assistant_tab(ctrl)

    layout.render_footer()


main()
