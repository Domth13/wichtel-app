"""
Wichtel-App - Hauptanwendung
Eine Streamlit-App für geheimes Weihnachtswichteln
"""
import streamlit as st
from config import APP_TITLE, APP_ICON
from models import DataManager
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

# Seitenkonfiguration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Weihnachtliches Theme anwenden
apply_christmas_theme()


def init_session_state():
    """Initialisiert den Session State"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_event' not in st.session_state:
        st.session_state.current_event = None


def main():
    """Hauptfunktion der App"""
    init_session_state()
    show_header()
    
    # Prüfe ob Passwort geändert werden muss
    if hasattr(st.session_state, 'show_password_change') and st.session_state.show_password_change:
        show_password_change_form()
        return
    
    # Prüfe ob Benutzer eingeloggt ist
    if st.session_state.user is None:
        show_login_form()
    else:
        user = st.session_state.user
        
        # Sidebar mit Benutzerinfo
        with st.sidebar:
            st.write(f"### 👤 {user.name}")
            st.write(f"📧 {user.email}")
            show_logout_button()
        
        # Hauptbereich
        if st.session_state.current_event is None:
            # Zeige Event-Liste und Erstellformular
            show_create_event_form(user)
            st.divider()
            show_event_list(user)
        else:
            # Zeige Event-Details
            events = DataManager.load_events()
            event = events.get(st.session_state.current_event)
            
            if event:
                show_event_details(event, user)
            else:
                st.error("❌ Event nicht gefunden")
                st.session_state.current_event = None
                st.rerun()


if __name__ == "__main__":
    main()