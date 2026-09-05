"""Local adaptation of streamlit-keyup 0.3.0; see LICENSE and README.md."""
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import declare_component

_component = declare_component("live_answers", path=str(Path(__file__).parent))


def st_keyup(label, value="", max_chars=45, key=None, debounce=100):
    """Keep answer state independent of the component's widget identity."""
    answer = _component(
        label=label, value=value, max_chars=max_chars, debounce=debounce,
        key=f"live_{key}", default=value,
    )
    if key is not None:
        st.session_state[key] = answer
    return answer
