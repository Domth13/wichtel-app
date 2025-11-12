"""
Wichtel-App - Hauptanwendung
Eine Streamlit-App für geheimes Weihnachtswichteln
"""
import streamlit as st
from config import APP_TITLE, APP_ICON
from models import DataManager
from link_service import LinkAuthService

# Seitenkonfiguration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Weihnachtliches Theme anwenden
from ui_components import (
    apply_christmas_theme,
    show_header,
    show_login_form,
    show_password_change_form,
    show_event_list,
    show_create_event_form,
    show_event_details,
    show_logout_button
)

apply_christmas_theme()


def init_session_state():
    """Initialisiert den Session State"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_event' not in st.session_state:
        st.session_state.current_event = None
    if 'link_token' not in st.session_state:
        st.session_state.link_token = None
    if 'auth_via_link' not in st.session_state:
        st.session_state.auth_via_link = False
    if 'admin_login' not in st.session_state:
        st.session_state.admin_login = False


def get_query_params():
    """Hilfsfunktion für Query-Parameter (Streamlit-Versionen kompatibel)"""
    if hasattr(st, "query_params"):
        return st.query_params
    return st.experimental_get_query_params()


def handle_link_auth():
    """Versucht Benutzer über Token-Query-Param einzuloggen"""
    params = get_query_params()
    token_param = params.get("token")

    token_value = None
    if isinstance(token_param, list) and token_param:
        token_value = token_param[0]
    elif isinstance(token_param, str):
        token_value = token_param

    if not token_value:
        return

    if (
        st.session_state.link_token == token_value
        and st.session_state.user is not None
        and not st.session_state.user.is_admin
    ):
        return

    resolved = LinkAuthService.resolve_token(token_value)
    if not resolved:
        st.error("Ungültiger oder deaktivierter Einladungslink.")
        return

    event, link = resolved
    users = DataManager.load_users()
    user = users.get(link.user_id)

    if not user:
        st.error("Kein Benutzer zu diesem Link gefunden.")
        return

    st.session_state.user = user
    st.session_state.current_event = event.id
    st.session_state.link_token = token_value
    st.session_state.auth_via_link = True
    st.session_state.admin_login = False
    if 'show_password_change' in st.session_state:
        st.session_state.show_password_change = False
    if 'temp_user' in st.session_state:
        del st.session_state['temp_user']


def render_public_entry():
    """Zeigt Infos für Teilnehmer ohne Admin-Login"""
    st.info("Bitte verwende deinen persönlichen Einladungslink, um direkt zum Event zu gelangen.")
    st.caption("Admins können sich über den Login anmelden.")

    if not st.session_state.admin_login:
        if st.button("Admin-Login öffnen"):
            st.session_state.admin_login = True
            st.rerun()
    else:
        show_login_form()


def render_admin_view(user):
    """Zeigt den kompletten Admin-Workflow"""
    with st.sidebar:
        st.write(f"### {user.name}")
        st.write(f" {user.email}")
        show_logout_button()

    if st.session_state.current_event is None:
        show_create_event_form(user)
        st.divider()
        show_event_list(user)
    else:
        events = DataManager.load_events()
        event = events.get(st.session_state.current_event)

        if event:
            show_event_details(event, user, admin_view=True)
        else:
            st.error("Event nicht gefunden")
            st.session_state.current_event = None
            st.rerun()


def render_participant_view(user):
    """Zeigt direkt das eingeladene Event"""
    with st.sidebar:
        st.write(f"### {user.name}")
        st.caption("Angemeldet über Einladungslink.")

    if not st.session_state.current_event:
        st.warning("Kein Event zu diesem Link gefunden.")
        return

    events = DataManager.load_events()
    event = events.get(st.session_state.current_event)

    if event and user.id in event.participant_ids:
        show_event_details(event, user, admin_view=False)
    else:
        st.error("Dieses Event ist nicht mehr verfügbar oder du bist kein Teilnehmer.")
        st.session_state.user = None
        st.session_state.auth_via_link = False
        st.session_state.link_token = None


def main():
    """Hauptfunktion der App"""
    init_session_state()
    show_header()
    handle_link_auth()
    
    # Prüfe ob Passwort geändert werden muss
    if hasattr(st.session_state, 'show_password_change') and st.session_state.show_password_change:
        show_password_change_form()
        return
    
    # Prüfe ob Benutzer eingeloggt ist
    if st.session_state.user is None:
        if st.session_state.admin_login:
            show_login_form()
        else:
            render_public_entry()
    else:
        user = st.session_state.user

        if user.is_admin:
            render_admin_view(user)
        else:
            render_participant_view(user)


if __name__ == "__main__":
    main()
