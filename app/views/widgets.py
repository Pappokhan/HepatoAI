import inspect

import streamlit as st


def stretch(fn) -> dict:
    """Full-width kwargs that work on both old (use_container_width) and new (width="stretch") Streamlit."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return {}
    if "width" in params:
        return {"width": "stretch"}
    if "use_container_width" in params:
        return {"use_container_width": True}
    return {}
