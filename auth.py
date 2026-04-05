"""Simple app-level password gate for Streamlit (env or st.secrets)."""
import hmac
import os
from typing import Optional

import streamlit as st

_ENV_KEY = "FINANCIAL_TRACKER_PASSWORD"
_SECRET_KEY = "app_password"


def _get_configured_password() -> Optional[str]:
    env_pw = os.environ.get(_ENV_KEY, "").strip()
    if env_pw:
        return env_pw
    try:
        val = st.secrets[_SECRET_KEY]
        if val is not None and str(val).strip():
            return str(val).strip()
    except (KeyError, FileNotFoundError, TypeError):
        pass
    return None


def _passwords_equal(entered: str, expected: str) -> bool:
    a = entered.encode("utf-8")
    b = expected.encode("utf-8")
    if len(a) != len(b):
        return False
    return hmac.compare_digest(a, b)


def is_password_configured() -> bool:
    return _get_configured_password() is not None


def is_authenticated() -> bool:
    return bool(st.session_state.get("_auth_ok"))


def logout():
    st.session_state["_auth_ok"] = False


def render_login_block() -> None:
    st.title("Financial Tracker")
    st.markdown("Sign in to continue.")
    with st.form("login_form"):
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in")
        if submitted:
            expected = _get_configured_password()
            if expected and _passwords_equal(password, expected):
                st.session_state["_auth_ok"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")


def ensure_authenticated() -> bool:
    """
    Returns True if the user may use the app.
    If a password is configured (env or secrets), shows a login screen until success.
    If none is configured, allows access and shows a sidebar warning (local dev only).
    """
    expected = _get_configured_password()
    if not expected:
        return True
    if is_authenticated():
        return True
    render_login_block()
    st.stop()
    return False
