"""
UI components for the Secret Santa app.
"""
import streamlit as st
from typing import List

from models import User, Event, DataManager
from wichtel_logic import WichtelLogic
from email_service import send_event_started_emails
from link_service import LinkAuthService, build_invite_url


def apply_christmas_theme():
    """Injects the CSS theme."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@700&family=Roboto:wght@400;700&display=swap');
        
        body {
        }
        .block-container {
            max-width: 900px;
            padding-top: 2rem;
            padding-bottom: 2rem;
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        }
        
        h1, h2, h3 {
            font-family: 'Mountains of Christmas', cursive;
            color: #2E7D32; /* Dark Green */
        }
        
        .stButton>button {
            background-color: #D32F2F; /* Festive Red */
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 28px;
            font-weight: bold;
            font-family: 'Roboto', sans-serif;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px 0 rgba(0,0,0,0.1);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px 0 rgba(0,0,0,0.15);
            background-color: #C62828; /* Darker Red */
        }
        
        .stButton>button[type="submit"] {
             background-color: #2E7D32; /* Dark Green */
        }
        .stButton>button[type="submit"]:hover {
             background-color: #1B5E20; /* Darker Green */
        }

        .wichtel-reveal {
            background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
            color: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            margin: 20px 0;
            font-family: 'Roboto', sans-serif;
            border: 2px dashed #FFD700; /* Gold dash */
            animation: revealAnimation 0.8s ease-out forwards;
        }

        @keyframes revealAnimation {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .header-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        .gift-box {
            font-size: 60px;
            text-align: center;
            padding-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_header():
    """Simple header with a Christmas gift emoji."""
    st.markdown(
        """
        <div class='header-container'>
            <div class='gift-box'>🎁</div>
            <h1>Wichtel App</h1>
            <p style='text-align: center; font-style: italic;'>
                Frohe Weihnachten und viel Spaß beim Wichteln!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


def show_login_form():
    """Login form for admins only."""
    st.subheader("Admin Login")
    with st.form("login_form"):
        email = st.text_input("E-Mail", placeholder="anna@example.com")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Anmelden", use_container_width=True)

        if submit:
            user = DataManager.authenticate(email, password)
            if not user:
                st.error("Anmeldedaten sind ungültig.")
                return

            if not user.password_changed:
                st.session_state.temp_user = user
                st.session_state.show_password_change = True
                st.rerun()
                return

            st.session_state.user = user
            if hasattr(st.session_state, "admin_login"):
                st.session_state.admin_login = False
            st.success(f"Willkommen, {user.name}!")
            st.rerun()


def show_password_change_form():
    """Password change dialog that is shown on first login."""
    st.subheader("Passwort ändern")
    st.info("Bitte wähle ein neues Passwort für deinen Account.")
    user = st.session_state.temp_user
    st.write(f"**Account:** {user.name} ({user.email})")

    with st.form("password_change_form"):
        new_password = st.text_input("Neues Passwort", type="password")
        confirm_password = st.text_input("Passwort bestätigen", type="password")
        submit = st.form_submit_button("Speichern", use_container_width=True)

        if not submit:
            return

        if not new_password:
            st.error("Bitte gib ein Passwort ein.")
            return
        if len(new_password) < 6:
            st.error("Passwort muss mindestens 6 Zeichen haben.")
            return
        if new_password != confirm_password:
            st.error("Passwörter stimmen nicht überein.")
            return

        user.password = new_password
        user.password_changed = True
        DataManager.update_user(user)
        st.session_state.user = user
        st.session_state.pop("temp_user", None)
        st.session_state.pop("show_password_change", None)
        st.success("Passwort gespeichert. Viel Spaß!")
        st.balloons()
        st.rerun()


def show_event_list(user: User):
    """List of events for the admin dashboard."""
    st.subheader(f"Hallo {user.name}!")
    events = WichtelLogic.get_user_events(user.id)

    if not events:
        st.info("Noch keine Events vorhanden.")
        return

    for event in events:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {event.title}")
                caption = f"{len(event.participant_ids)} Teilnehmer"
                if event.gift_value:
                    caption += f"  ·  Wert: {event.gift_value}"
                st.caption(caption)
            with col2:
                if event.is_started:
                    st.success("Gestartet")
                else:
                    st.warning("Wartet")

            button_cols = st.columns([3, 1] if user.is_admin else [1])
            with button_cols[0]:
                if st.button(
                    "Event öffnen",
                    key=f"open_{event.id}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state.current_event = event.id
                    st.rerun()

            if user.is_admin and len(button_cols) > 1:
                with button_cols[1]:
                    if st.button("Löschen", key=f"delete_{event.id}"):
                        st.session_state.delete_confirm = event.id
                        st.rerun()

            if (
                hasattr(st.session_state, "delete_confirm")
                and st.session_state.delete_confirm == event.id
            ):
                st.warning(f"Event '{event.title}' wirklich löschen?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button(
                        "Ja, löschen",
                        key=f"confirm_delete_{event.id}",
                        use_container_width=True,
                    ):
                        DataManager.delete_event(event.id)
                        del st.session_state.delete_confirm
                        st.success("Event gelöscht.")
                        st.rerun()
                with col_no:
                    if st.button(
                        "Abbrechen",
                        key=f"cancel_delete_{event.id}",
                        use_container_width=True,
                    ):
                        del st.session_state.delete_confirm
                        st.rerun()
        st.divider()


def show_create_event_form(user: User):
    """Form for creating a new event (admins only)."""
    if not user.is_admin:
        return

    with st.expander("Neues Event erstellen", expanded=True):
        title = st.text_input("Event-Titel", placeholder="Weihnachtswichteln 2025")
        gift_value = st.text_input("Wert der Geschenke (optional)", placeholder="z.B. ca. 15€")
        
        st.write("Teilnehmer auswählen:")
        users = DataManager.load_users()
        user_options = {uid: u.name for uid, u in users.items() if uid != user.id}
        selected_users = st.multiselect(
            "Teilnehmer",
            options=list(user_options.keys()),
            format_func=lambda uid: user_options[uid],
            label_visibility="collapsed",
        )

        if st.button(
            "Event erstellen",
            type="primary",
            use_container_width=True,
            key="create_event_btn",
        ):
            if not title or not selected_users:
                st.warning("Bitte Titel und mindestens einen Teilnehmer auswählen.")
                return

            participant_ids = [user.id] + selected_users
            event = DataManager.create_event(title, user.id, participant_ids, gift_value)
            LinkAuthService.ensure_links_for_event(event)
            st.success(f"Event '{title}' erstellt.")
            st.session_state.current_event = event.id
            st.rerun()


def show_event_details(event: Event, user: User, admin_view: bool = False):
    """Details page for a given event."""
    if admin_view:
        if st.button("Zurück zur Liste"):
            st.session_state.current_event = None
            st.rerun()
        LinkAuthService.ensure_links_for_event(event)
    else:
        st.caption("Angemeldet über Einladungslink.")

    st.markdown(f"## {event.title}")
    st.divider()

    if not event.is_started:
        st.warning("Das Event wurde noch nicht gestartet.")
        if admin_view and user.is_admin:
            if st.button(
                "Wichtel-Zuweisungen starten",
                type="primary",
                use_container_width=True,
            ):
                WichtelLogic.assign_wichtel_random(event)
                send_event_started_emails(event)
                st.success("Zuweisungen erstellt und Mails versendet.")
                st.balloons()
                st.rerun()
    else:
        assignment = WichtelLogic.get_assignment_for_user(event, user.id)
        if assignment:
            if not assignment.revealed:
                if st.button(
                    "Meinen Wichtel anzeigen",
                    type="primary",
                    use_container_width=True,
                ):
                    WichtelLogic.reveal_assignment(event, user.id)
                    st.rerun()
            else:
                receiver_name = WichtelLogic.get_receiver_name(assignment)
                gift_value_html = f"<p style='font-size: 16px; margin-top: 15px; opacity: 0.9;'>Geschenkwert: {event.gift_value}</p>" if event.gift_value else ""
                st.markdown(
                    f"""
                    <div class='wichtel-reveal'>
                        Du wichtelst für:<br>
                        <strong>{receiver_name}</strong>
                        {gift_value_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()
    users = DataManager.load_users()

    with st.expander("Event Informationen", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Teilnehmer: {len(event.participant_ids)}")
            if event.gift_value:
                st.write(f"Geschenkwert: {event.gift_value}")
        with col2:
            creator = users.get(event.created_by)
            st.write(f"Erstellt von: {creator.name if creator else 'Unbekannt'}")

    with st.expander("Alle Teilnehmer", expanded=False):
        for pid in event.participant_ids:
            participant = users.get(pid)
            if participant:
                st.write(f"- {participant.name}")

    if admin_view:
        st.divider()
        with st.expander("Einladungslinks verwalten", expanded=False):
            for pid in event.participant_ids:
                participant = users.get(pid)
                if not participant:
                    continue
                link = LinkAuthService.get_or_create_link(event, pid)
                invite_url = build_invite_url(link.token)
                label = f"{participant.name} ({participant.email})"
                st.text_input(
                    label,
                    value=invite_url,
                    key=f"invite_url_{event.id}_{pid}",
                    disabled=True,
                )
                if st.button(
                    f"Link erneuern für {participant.name}",
                    key=f"refresh_link_{event.id}_{pid}",
                ):
                    LinkAuthService.refresh_link(event, pid)
                    st.success("Link erneuert.")
                    st.rerun()
                st.write("")


def show_logout_button():
    """Sidebar logout button."""
    st.sidebar.divider()
    if st.sidebar.button("Abmelden", use_container_width=True):
        st.session_state.clear()
        st.rerun()
