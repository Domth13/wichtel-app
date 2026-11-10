"""
Kleine Flash-Nachrichten, die einen st.rerun() überleben.

st.success()/st.balloons() direkt vor st.rerun() werden von Streamlit
verworfen. Deshalb wird die Nachricht im Session State geparkt und im
nächsten Run ausgegeben.
"""
import streamlit as st


def set_flash(kind: str = "success", message: str = "", balloons: bool = False, details=None):
    st.session_state["_flash"] = {
        "kind": kind if kind in {"success", "info", "warning", "error"} else "info",
        "message": message or "",
        "balloons": bool(balloons),
        "details": list(details or []),
    }


def request_balloons():
    st.session_state["_balloons"] = True


def render_flash():
    data = st.session_state.pop("_flash", None)
    if data:
        message = data.get("message") or ""
        if message:
            renderer = getattr(st, data.get("kind", "info"), st.info)
            renderer(message)
        details = data.get("details") or []
        if details:
            st.warning("\n".join(f"- {item}" for item in details))
        if data.get("balloons"):
            st.balloons()

    if st.session_state.pop("_balloons", False):
        st.balloons()
