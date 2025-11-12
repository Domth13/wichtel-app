"""
Language and translation management for the Wichtel App.
"""
import streamlit as st
from streamlit.components.v1 import html
import json

# Define supported languages
LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
}

def init_language_support():
    """
    Initializes language support by detecting browser language.
    Checks for a 'lang' query parameter first, then uses JavaScript
    to get the browser language and re-run the app with the parameter.
    """
    if 'language' in st.session_state:
        return

    query_params = st.query_params
    lang_from_query = query_params.get("lang")

    if lang_from_query:
        lang_code = lang_from_query[0] if isinstance(lang_from_query, list) else lang_from_query
        lang_code = lang_code.split('-')[0].lower()
        if lang_code in LANGUAGES:
            st.session_state.language = lang_code
            return

    # If no valid lang parameter, use JS to get it and reload
    js_code = f'''
        <script>
            (function() {{
                if (!window.location.search.includes('lang=')) {{
                    const lang = navigator.language || navigator.userLanguage;
                    const mainLang = lang.split('-')[0];
                    const supportedLangs = {json.dumps(list(LANGUAGES.keys()))};
                    let targetLang = 'de'; # default
                    if (supportedLangs.includes(mainLang)) {{
                        targetLang = mainLang;
                    }}
                    
                    const url = new URL(window.location);
                    url.searchParams.set('lang', targetLang);
                    window.location.href = url.href;
                }}
            }})();
        </script>
    '''
    html(js_code, height=0)
    st.session_state.language = "de" # Default while JS runs


# Translation dictionary
# Add all user-facing strings here
TRANSLATIONS = {
    "de": {
        "app_title": "Wichtel App",
        "app_slogan": "Frohe Weihnachten und viel Spaß beim Wichteln!",
        "admin_login": "Admin Login",
        "email_label": "E-Mail",
        "password_label": "Passwort",
        "login_button": "Anmelden",
        "invalid_credentials": "Anmeldedaten sind ungültig.",
        "welcome": "Willkommen, {name}!",
        "change_password_header": "Passwort ändern",
        "change_password_info": "Bitte wähle ein neues Passwort für deinen Account.",
        "account": "Account",
        "new_password": "Neues Passwort",
        "confirm_password": "Passwort bestätigen",
        "save_button": "Speichern",
        "password_empty": "Bitte gib ein Passwort ein.",
        "password_too_short": "Passwort muss mindestens 6 Zeichen haben.",
        "passwords_not_match": "Passwörter stimmen nicht überein.",
        "password_saved": "Passwort gespeichert. Viel Spaß!",
        "hello": "Hallo {name}!",
        "no_events_yet": "Noch keine Events vorhanden.",
        "participants": "{count} Teilnehmer",
        "gift_value": "Wert: {value}",
        "started": "Gestartet",
        "waiting": "Wartet",
        "open_event": "Event öffnen",
        "delete_button": "Löschen",
        "confirm_delete_event": "Event '{title}' wirklich löschen?",
        "yes_delete": "Ja, löschen",
        "cancel": "Abbrechen",
        "event_deleted": "Event gelöscht.",
        "create_new_event": "Neues Event erstellen",
        "event_title": "Event-Titel",
        "event_title_placeholder": "Weihnachtswichteln 2025",
        "gift_value_optional": "Wert der Geschenke (optional)",
        "gift_value_placeholder": "z.B. ca. 15€",
        "select_participants": "Teilnehmer auswählen:",
        "participants_label": "Teilnehmer",
        "create_event_button": "Event erstellen",
        "title_participants_missing": "Bitte Titel und mindestens einen Teilnehmer auswählen.",
        "event_created": "Event '{title}' erstellt.",
        "back_to_list": "Zurück zur Liste",
        "logged_in_via_invite": "Angemeldet über Einladungslink.",
        "event_not_started": "Das Event wurde noch nicht gestartet.",
        "start_assignments": "Wichtel-Zuweisungen starten",
        "assignments_sent": "Zuweisungen erstellt und Mails versendet.",
        "show_my_wichtel": "Meinen Wichtel anzeigen",
        "you_wichtel_for": "Du wichtelst für:",
        "event_information": "Event Informationen",
        "created_by": "Erstellt von",
        "unknown": "Unbekannt",
        "all_participants": "Alle Teilnehmer",
        "manage_invite_links": "Einladungslinks verwalten",
        "refresh_link": "Link erneuern für {name}",
        "link_refreshed": "Link erneuert.",
        "logout_button": "Abmelden",
        "email_invite_subject": "Einladung zum Wichtel-Event: {event_title}",
        "email_invite_heading": "Wichtel-Einladung!",
        "email_invite_subheading": "Du wurdest eingeladen!",
        "email_invite_body_hello": "Hallo!",
        "email_invite_body_event": "Du wurdest zum Wichtel-Event <strong>\"{event_title}\"</strong> eingeladen!",
        "email_invite_body_waiting": "Das Event wurde erstellt und wartet darauf, gestartet zu werden. Du erhältst eine weitere E-Mail, sobald die Wichtel-Zuweisungen erfolgt sind.",
        "email_invite_button": "Zum Event",
        "email_invite_footer": "Frohe Weihnachten und viel Spaß beim Wichteln!",
        "email_started_subject": "Dein Wichtel wartet auf dich: {event_title}",
        "email_started_heading": "Los geht's!",
        "email_started_subheading": "Die Wichtel wurden zugewiesen!",
        "email_started_body_hello": "Hallo!",
        "email_started_body_event": "Das Wichtel-Event <strong>\"{event_title}\"</strong> wurde gestartet!",
        "email_started_body_assignment": "Deine Wichtel-Zuweisung wartet auf dich. Klicke auf den Button unten, um zu erfahren, für wen du ein Geschenk besorgen darfst!",
        "email_started_button": "Meinen Wichtel zeigen!",
        "email_started_footer": "Viel Spaß beim Geschenke besorgen!",
        "gift_value_display": "Geschenkwert: {value}",
        "invalid_invite_link": "Ungültiger oder deaktivierter Einladungslink.",
        "no_user_for_link": "Kein Benutzer zu diesem Link gefunden.",
        "use_personal_link_info": "Bitte verwende deinen persönlichen Einladungslink, um direkt zum Event zu gelangen.",
        "admins_can_login_caption": "Admins können sich über den Login anmelden.",
        "open_admin_login": "Admin-Login öffnen",
        "event_not_found": "Event nicht gefunden",
        "no_event_for_link": "Kein Event zu diesem Link gefunden.",
        "event_unavailable_or_not_participant": "Dieses Event ist nicht mehr verfügbar oder du bist kein Teilnehmer.",
        "language_selector_label": "Sprache",
    },
    "en": {
        "app_title": "Secret Santa App",
        "app_slogan": "Merry Christmas and have fun with Secret Santa!",
        "admin_login": "Admin Login",
        "email_label": "E-Mail",
        "password_label": "Password",
        "login_button": "Login",
        "invalid_credentials": "Invalid credentials.",
        "welcome": "Welcome, {name}!",
        "change_password_header": "Change Password",
        "change_password_info": "Please choose a new password for your account.",
        "account": "Account",
        "new_password": "New Password",
        "confirm_password": "Confirm Password",
        "save_button": "Save",
        "password_empty": "Please enter a password.",
        "password_too_short": "Password must be at least 6 characters long.",
        "passwords_not_match": "Passwords do not match.",
        "password_saved": "Password saved. Have fun!",
        "hello": "Hello {name}!",
        "no_events_yet": "No events available yet.",
        "participants": "{count} participants",
        "gift_value": "Value: {value}",
        "started": "Started",
        "waiting": "Waiting",
        "open_event": "Open Event",
        "delete_button": "Delete",
        "confirm_delete_event": "Really delete event '{title}'?",
        "yes_delete": "Yes, delete",
        "cancel": "Cancel",
        "event_deleted": "Event deleted.",
        "create_new_event": "Create New Event",
        "event_title": "Event Title",
        "event_title_placeholder": "Christmas Secret Santa 2025",
        "gift_value_optional": "Gift Value (optional)",
        "gift_value_placeholder": "e.g., approx. 15€",
        "select_participants": "Select participants:",
        "participants_label": "Participants",
        "create_event_button": "Create Event",
        "title_participants_missing": "Please select a title and at least one participant.",
        "event_created": "Event '{title}' created.",
        "back_to_list": "Back to List",
        "logged_in_via_invite": "Logged in via invite link.",
        "event_not_started": "The event has not started yet.",
        "start_assignments": "Start Secret Santa Assignments",
        "assignments_sent": "Assignments created and emails sent.",
        "show_my_wichtel": "Show my Secret Santa",
        "you_wichtel_for": "You are Secret Santa for:",
        "event_information": "Event Information",
        "created_by": "Created by",
        "unknown": "Unknown",
        "all_participants": "All Participants",
        "manage_invite_links": "Manage Invite Links",
        "refresh_link": "Refresh link for {name}",
        "link_refreshed": "Link refreshed.",
        "logout_button": "Logout",
        "email_invite_subject": "Invitation to Secret Santa Event: {event_title}",
        "email_invite_heading": "Secret Santa Invitation!",
        "email_invite_subheading": "You have been invited!",
        "email_invite_body_hello": "Hello!",
        "email_invite_body_event": "You have been invited to the Secret Santa event <strong>\"{event_title}\"</strong>!",
        "email_invite_body_waiting": "The event has been created and is waiting to be started. You will receive another email once the Secret Santa assignments have been made.",
        "email_invite_button": "To the Event",
        "email_invite_footer": "Merry Christmas and have fun with Secret Santa!",
        "email_started_subject": "Your Secret Santa is waiting for you: {event_title}",
        "email_started_heading": "Let's go!",
        "email_started_subheading": "The Secret Santas have been assigned!",
        "email_started_body_hello": "Hello!",
        "email_started_body_event": "The Secret Santa event <strong>\"{event_title}\"</strong> has started!",
        "email_started_body_assignment": "Your Secret Santa assignment is waiting for you. Click the button below to find out who you get to buy a gift for!",
        "email_started_button": "Show my Secret Santa!",
        "email_started_footer": "Have fun buying gifts!",
        "gift_value_display": "Gift Value: {value}",
        "invalid_invite_link": "Invalid or deactivated invitation link.",
        "no_user_for_link": "No user found for this link.",
        "use_personal_link_info": "Please use your personal invitation link to go directly to the event.",
        "admins_can_login_caption": "Admins can log in via the login form.",
        "open_admin_login": "Open Admin Login",
        "event_not_found": "Event not found",
        "no_event_for_link": "No event found for this link.",
        "event_unavailable_or_not_participant": "This event is no longer available or you are not a participant.",
        "language_selector_label": "Language",
    },
}


def get_translator():
    """
    Returns a translation function based on the current language in session state.
    Initializes session state language if not set.
    """
    if "language" not in st.session_state:
        st.session_state.language = "de"  # Default language

    lang_code = st.session_state.language
    translations = TRANSLATIONS.get(lang_code, TRANSLATIONS["de"]) # Fallback to German

    def _(key, **kwargs):
        """
        Translates a given key.
        Supports f-string like formatting with kwargs.
        """
        translated_string = translations.get(key, key) # Fallback to key if not found
        return translated_string.format(**kwargs) if kwargs else translated_string

    return _

def set_language(lang_code: str):
    """Sets the current language in session state."""
    if lang_code in LANGUAGES:
        st.session_state.language = lang_code