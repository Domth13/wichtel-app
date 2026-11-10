"""
Einmaliger Admin-Bootstrap für ein frisches Deployment.

Wenn noch kein Admin existiert, wird er aus ADMIN_EMAIL / ADMIN_PASSWORD
angelegt. Vorhandene Daten werden nie überschrieben.
"""
import os

import streamlit as st

from models import DataManager
from security import hash_password, is_password_hash


def ensure_admin() -> None:
    """Legt bei Bedarf den ersten Admin aus den Secrets an."""
    users = DataManager.load_users()

    # Einmalige Migration: eventuell noch vorhandene Klartext-Passwörter
    # (auch von Teilnehmern, die sich nie einloggen) durch Hashes ersetzen.
    if any(not is_password_hash(user.password) for user in users.values()):
        for user in users.values():
            if not is_password_hash(user.password):
                user.password = hash_password(user.password)
        DataManager.save_users(users)

    if any(user.is_admin for user in users.values()):
        st.session_state.pop("bootstrap_missing", None)
        st.session_state.pop("bootstrap_error", None)
        return

    email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD") or ""
    name = (os.getenv("ADMIN_NAME") or "Admin").strip()

    if not email or not password:
        st.session_state["bootstrap_missing"] = True
        return

    if len(password) < 8:
        st.session_state["bootstrap_error"] = "password_too_short"
        return

    try:
        existing = DataManager.get_user_by_email(email)
        if existing:
            existing.is_admin = True
            existing.password = hash_password(password)
            existing.password_changed = False
            DataManager.update_user(existing)
        else:
            DataManager.create_user(
                name=name,
                email=email,
                password=password,
                is_admin=True,
            )
    except ValueError as exc:
        st.session_state["bootstrap_error"] = str(exc)
        return

    st.session_state.pop("bootstrap_missing", None)
    st.session_state.pop("bootstrap_error", None)
    st.session_state["bootstrap_created"] = True
