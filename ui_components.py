"""
UI-Komponenten für die Wichtel-App
"""
import streamlit as st
from models import User, Event, DataManager
from wichtel_logic import WichtelLogic
from email_service import send_event_started_emails
from typing import List


def apply_christmas_theme():
    """Wendet weihnachtliches CSS-Styling an"""
    st.markdown("""
        <style>
        /* Container mit max-width für große Bildschirme */
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Schönere Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 10px 25px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102,126,234,0.5);
        }
        
        /* Wichtel-Enthüllungs-Box */
        .wichtel-reveal {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        /* Geschenk-Animation */
        .gift-box {
            font-size: 80px;
            text-align: center;
            animation: bounce 1s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        /* Zentrierter Header */
        .header-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Multiselect nicht zu groß werden lassen */
        .stMultiSelect [data-baseweb="select"] {
            max-height: 200px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)


def show_header():
    """Zeigt den App-Header"""
    st.markdown("""
        <div class='header-container'>
            <div class='gift-box'>🎁</div>
            <h1>🎄 Wichtel App 🎅</h1>
            <p style='text-align: center; font-style: italic;'>Frohe Weihnachten und viel Spaß beim Wichteln! ✨</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()


def show_login_form():
    """Zeigt das Login-Formular"""
    st.subheader("🔑 Anmeldung")
    
    with st.form("login_form"):
        email = st.text_input("📧 E-Mail", placeholder="deine@email.de")
        password = st.text_input("🔒 Passwort", type="password")
        submit = st.form_submit_button("Anmelden", use_container_width=True)
        
        if submit:
            user = DataManager.authenticate(email, password)
            if user:
                # Prüfe ob Passwort geändert werden muss
                if not user.password_changed:
                    st.session_state.temp_user = user
                    st.session_state.show_password_change = True
                    st.rerun()
                else:
                    st.session_state.user = user
                    st.success(f"Willkommen, {user.name}! 🎉")
                    st.rerun()
            else:
                st.error("❌ Ungültige Anmeldedaten")


def show_password_change_form():
    """Zeigt das Formular zur Passwortänderung beim ersten Login"""
    st.subheader("🔐 Passwort ändern")
    st.info("👋 Willkommen! Bitte wähle ein neues Passwort für deinen Account.")
    
    user = st.session_state.temp_user
    st.write(f"**Account:** {user.name} ({user.email})")
    
    with st.form("password_change_form"):
        new_password = st.text_input("🔒 Neues Passwort", type="password")
        confirm_password = st.text_input("🔒 Passwort bestätigen", type="password")
        submit = st.form_submit_button("Passwort speichern", use_container_width=True)
        
        if submit:
            if not new_password:
                st.error("❌ Bitte gib ein Passwort ein")
            elif len(new_password) < 6:
                st.error("❌ Passwort muss mindestens 6 Zeichen lang sein")
            elif new_password != confirm_password:
                st.error("❌ Passwörter stimmen nicht überein")
            else:
                user.password = new_password
                user.password_changed = True
                DataManager.update_user(user)
                st.session_state.user = user
                del st.session_state.temp_user
                del st.session_state.show_password_change
                st.success("✅ Passwort erfolgreich geändert!")
                st.balloons()
                st.rerun()


def show_event_list(user: User):
    """Zeigt die Liste der Events für einen Benutzer"""
    st.subheader(f"Hallo, {user.name}! 👋")
    
    events = WichtelLogic.get_user_events(user.id)
    
    if not events:
        st.info("📭 Du hast noch keine Wichtel-Events. Erstelle eins oder warte auf eine Einladung!")
    
    for event in events:
        with st.container():
            # Kompakte Darstellung mit Event-Titel und Status
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🎄 {event.title}")
                st.caption(f"👥 {len(event.participant_ids)} Teilnehmer")
            
            with col2:
                if event.is_started:
                    st.success("🎁 Aktiv")
                else:
                    st.warning("⏳ Wartet")
            
            # Buttons
            button_cols = st.columns([3, 1] if user.is_admin else [1])
            
            with button_cols[0]:
                if st.button(f"📖 Event öffnen", key=f"open_{event.id}", use_container_width=True, type="primary"):
                    st.session_state.current_event = event.id
                    st.rerun()
            
            # Löschen-Button nur für Admins
            if user.is_admin and len(button_cols) > 1:
                with button_cols[1]:
                    if st.button("🗑️", key=f"delete_{event.id}", help="Event löschen"):
                        st.session_state.delete_confirm = event.id
                        st.rerun()
            
            # Bestätigungs-Dialog für Löschen
            if hasattr(st.session_state, 'delete_confirm') and st.session_state.delete_confirm == event.id:
                st.warning(f"⚠️ Event '{event.title}' wirklich löschen?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Ja, löschen", key=f"confirm_delete_{event.id}", use_container_width=True):
                        DataManager.delete_event(event.id)
                        del st.session_state.delete_confirm
                        st.success("Event gelöscht!")
                        st.rerun()
                with col_no:
                    if st.button("❌ Abbrechen", key=f"cancel_delete_{event.id}", use_container_width=True):
                        del st.session_state.delete_confirm
                        st.rerun()
            
            st.divider()


def show_create_event_form(user: User):
    """Zeigt das Formular zum Erstellen eines Events (nur für Admins)"""
    if not user.is_admin:
        return  # Nur Admins können Events erstellen
    
    with st.expander("➕ Neues Wichtel-Event erstellen", expanded=False):
        title = st.text_input("🎄 Event-Titel", placeholder="Weihnachtswichteln 2025", key="event_title")
        
        st.write("👥 **Teilnehmer auswählen:**")
        st.caption("Wähle die Personen aus, die am Wichteln teilnehmen sollen")
        
        users = DataManager.load_users()
        user_options = {uid: u.name for uid, u in users.items() if uid != user.id}
        
        selected_users = st.multiselect(
            "Teilnehmer:",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x],
            key="selected_users",
            label_visibility="collapsed"
        )
        
        # Extra Abstand vor dem Button
        st.write("")
        st.write("")
        
        if st.button("🎁 Event erstellen", type="primary", use_container_width=True, key="create_event_btn"):
            if title and selected_users:
                # Füge den Ersteller hinzu
                participant_ids = [user.id] + selected_users
                event = DataManager.create_event(title, user.id, participant_ids)
                st.success(f"✅ Event '{title}' wurde erstellt!")
                st.balloons()
                # Springe direkt ins Event
                st.session_state.current_event = event.id
                st.rerun()
            else:
                st.warning("⚠️ Bitte Titel eingeben und mindestens einen Teilnehmer auswählen")


def show_event_details(event: Event, user: User):
    """Zeigt die Details eines Events"""
    # Zurück-Button
    if st.button("⬅️ Zurück zur Übersicht"):
        st.session_state.current_event = None
        st.rerun()
    
    st.markdown(f"## 🎄 {event.title}")
    st.divider()
    
    # Event-Aktionen prominent oben
    if not event.is_started:
        st.warning("⏳ Das Event wurde noch nicht gestartet.")
        
        # Nur Admins können Zuweisungen starten - PROMINENT
        if user.is_admin:
            st.write("")  # Spacing
            if st.button("🎲 Wichtel-Zuweisungen jetzt starten!", type="primary", use_container_width=True):
                WichtelLogic.assign_wichtel_random(event)
                # E-Mail-Versand
                send_event_started_emails(event)
                st.success("✅ Zuweisungen wurden erstellt und E-Mails versendet!")
                st.balloons()
                st.rerun()
            st.write("")  # Spacing
    else:
        # Zeige Zuweisung - PROMINENT
        assignment = WichtelLogic.get_assignment_for_user(event, user.id)
        
        if assignment:
            if not assignment.revealed:
                st.write("")  # Spacing
                if st.button("🎅 Meinen Wichtel zeigen!", type="primary", use_container_width=True):
                    WichtelLogic.reveal_assignment(event, user.id)
                    st.rerun()
                st.write("")  # Spacing
            else:
                receiver_name = WichtelLogic.get_receiver_name(assignment)
                st.write("")  # Spacing
                st.markdown(f"""
                    <div class='wichtel-reveal'>
                        Du wichtelst für:<br>
                        🎁 {receiver_name} 🎁
                    </div>
                """, unsafe_allow_html=True)
                st.write("")  # Spacing
    
    st.divider()
    
    # Event-Informationen kompakt
    users = DataManager.load_users()
    
    with st.expander("ℹ️ Event-Informationen", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**👥 Teilnehmer:** {len(event.participant_ids)}")
        with col2:
            creator = users.get(event.created_by)
            st.write(f"**👤 Ersteller:** {creator.name if creator else 'Unbekannt'}")
    
    # Teilnehmerliste
    with st.expander("👥 Alle Teilnehmer anzeigen", expanded=False):
        for pid in event.participant_ids:
            participant = users.get(pid)
            if participant:
                st.write(f"• {participant.name}")


def show_logout_button():
    """Zeigt den Logout-Button"""
    st.sidebar.divider()
    if st.sidebar.button("🚪 Abmelden", use_container_width=True):
        st.session_state.clear()
        st.rerun()