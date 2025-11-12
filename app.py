"""
Wichtel-App - Hauptanwendung
Eine Streamlit-App für geheimes Weihnachtswichteln
"""
import streamlit as st
from config import APP_TITLE, APP_ICON
from models import DataManager
from link_service import LinkAuthService
from language import LANGUAGES, get_translator, set_language, init_language_support

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
    show_language_selector,
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


def handle_link_auth(_):
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
        st.error(_("invalid_invite_link"))
        return

    event, link = resolved
    users = DataManager.load_users()
    user = users.get(link.user_id)

    if not user:
        st.error(_("no_user_for_link"))
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


def render_public_entry(_):
    """Zeigt Infos für Teilnehmer ohne Admin-Login"""
    st.info(_("use_personal_link_info"))
    st.caption(_("admins_can_login_caption"))

    if not st.session_state.admin_login:
        if st.button(_("open_admin_login")):
            st.session_state.admin_login = True
            st.rerun()
    else:
        show_login_form(_)


def render_admin_view(user, _):
    """Zeigt den kompletten Admin-Workflow"""
    with st.sidebar:
        st.write(f"### {user.name}")
        st.write(f" {user.email}")
        show_logout_button(_)

    if st.session_state.current_event is None:
        show_create_event_form(user, _)
        st.divider()
        show_event_list(user, _)
    else:
        events = DataManager.load_events()
        event = events.get(st.session_state.current_event)

        if event:
            show_event_details(event, user, _, admin_view=True)
        else:
            st.error(_("event_not_found"))
            st.session_state.current_event = None
            st.rerun()


def render_participant_view(user, _):
    """Zeigt direkt das eingeladene Event"""
    with st.sidebar:
        st.write(f"### {user.name}")
        st.caption(_("logged_in_via_invite"))

    if not st.session_state.current_event:
        st.warning(_("no_event_for_link"))
        return

    events = DataManager.load_events()
    event = events.get(st.session_state.current_event)

    if event and user.id in event.participant_ids:
        show_event_details(event, user, _, admin_view=False)
    else:
        st.error(_("event_unavailable_or_not_participant"))
        st.session_state.user = None
        st.session_state.auth_via_link = False
        st.session_state.link_token = None


def main():
    """Hauptfunktion der App"""
    init_language_support()
    _ = get_translator()

    show_language_selector(_)
    
    init_session_state()
    handle_link_auth(_)
    
    st.title(_("app_title"))
    st.caption(_("app_slogan"))
    st.divider()

    # Prüfe ob Passwort geändert werden muss
    if hasattr(st.session_state, 'show_password_change') and st.session_state.show_password_change:
        show_password_change_form(_)
        return
    
    # Prüfe ob Benutzer eingeloggt ist
    if st.session_state.user is None:
        if st.session_state.admin_login:
            show_login_form(_)
        else:
            render_public_entry(_)
    else:
        user = st.session_state.user

        if user.is_admin:
            render_admin_view(user, _)
        else:
            render_participant_view(user, _)


if __name__ == "__main__":
    main()