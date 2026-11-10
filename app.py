"""
Wichtel-App - Hauptanwendung
Eine Streamlit-App für geheimes Weihnachtswichteln.
"""
import html

import streamlit as st

from config import APP_ICON, APP_TITLE

# Muss der erste Streamlit-Befehl sein; deshalb vor den App-Modulen.
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Streamlit 1.67 wird für horizontale Container und die Navigation benötigt.
# Bei einem versehentlichen Start mit einer globalen Altversion zeigen wir
# eine konkrete Anleitung statt eines schwer verständlichen Tracebacks.
from packaging.version import Version  # noqa: E402

if Version(st.__version__) < Version("1.67.0"):
    st.error(
        f"Diese App benötigt Streamlit 1.67.0 oder neuer; gestartet wurde "
        f"Version {st.__version__}. Bitte die App beenden und im Projektordner "
        "mit `start-windows.bat` starten (oder siehe README für PowerShell und Git Bash). "
        "Falls die Projektumgebung noch fehlt, siehe README unter Schnellstart."
    )
    st.stop()

from bootstrap import ensure_admin  # noqa: E402
from flash import render_flash, set_flash  # noqa: E402
from language import get_translator, init_language_support  # noqa: E402
from link_service import LinkAuthService  # noqa: E402
from models import DataManager  # noqa: E402
from storage_cache import StorageUnavailableError, clear as clear_storage_cache  # noqa: E402
from ui_components import (  # noqa: E402
    apply_christmas_theme,
    show_account_settings,
    show_admin_side_panel,
    show_create_event_form,
    show_event_details,
    show_event_list,
    show_login_form,
    show_password_change_form,
    show_topbar,
    show_user_management,
)
from wichtel_logic import WichtelLogic  # noqa: E402

apply_christmas_theme()


def init_session_state():
    defaults = {
        "user": None,
        "current_event": None,
        "link_token": None,
        "auth_via_link": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _clear_auth():
    for key in ("user", "current_event", "link_token", "auth_via_link"):
        st.session_state.pop(key, None)


def _get_token_param():
    token = st.query_params.get("token")
    if isinstance(token, list):
        return token[0] if token else None
    return token


def handle_link_auth(_):
    """Authentifiziert Teilnehmer über ihren persönlichen Link."""
    user = st.session_state.get("user")
    token_in_session = st.session_state.get("link_token")

    # Bereits eingeloggte Teilnehmer bei jedem Run erneut prüfen.
    # So werden erneuerte/deaktivierte Links wirklich ungültig.
    if st.session_state.get("auth_via_link") and user and token_in_session:
        if not LinkAuthService.token_is_active(token_in_session, user.id):
            language = st.session_state.get("language", "de")
            _clear_auth()
            st.query_params.clear()
            st.query_params["lang"] = language
            set_flash("warning", _("session_revoked"))
            st.rerun()

    token_value = _get_token_param()
    if not token_value:
        return

    if (
        st.session_state.get("link_token") == token_value
        and st.session_state.get("user") is not None
    ):
        return

    resolved = LinkAuthService.resolve_token(token_value)
    if not resolved:
        st.error(_("invalid_invite_link"))
        return

    event, link = resolved
    if link.user_id not in event.participant_ids:
        st.error(_("event_unavailable_or_not_participant"))
        return

    users = DataManager.load_users()
    participant = users.get(link.user_id)
    if not participant:
        st.error(_("no_user_for_link"))
        return

    st.session_state.user = participant
    st.session_state.current_event = event.id
    st.session_state.link_token = token_value
    st.session_state.auth_via_link = True
    st.session_state.pop("show_password_change", None)
    st.session_state.pop("temp_user", None)


def render_hero(_, compact: bool = False):
    title = html.escape(_("app_title"))
    if compact:
        st.markdown(
            f'<div class="hero" style="padding: 0.1rem 0 0.6rem;">'
            f'<h1 style="font-size: 2.2rem;">🎄 {title}</h1></div>',
            unsafe_allow_html=True,
        )
    else:
        slogan = html.escape(_("app_slogan"))
        st.markdown(
            f'<div class="hero"><div class="hero-emoji">🎄</div>'
            f"<h1>{title}</h1><p>{slogan}</p></div>",
            unsafe_allow_html=True,
        )


def render_storage_error(_):
    st.error(_("storage_unavailable_title"))
    st.caption(_("storage_unavailable_hint"))
    if st.button(_("retry_connection"), type="primary"):
        clear_storage_cache()
        st.rerun()


def render_public_entry(_):
    st.markdown(
            '<div class="landing-layout">'
            f'<div class="landing-card"><div class="landing-icon">✉️</div>'
            f"<h3>{html.escape(_('landing_title'))}</h3>"
            f"<p>{html.escape(_('use_personal_link_info'))}</p></div>"
            '<div class="landing-instructions">'
            f'<div class="section-label">{html.escape(_("public_steps_title"))}</div>'
            f'<div class="side-steps">'
            f'<div class="side-step"><span class="step-num">1</span><strong>{html.escape(_("public_step_1"))}</strong></div>'
            f'<div class="side-step"><span class="step-num">2</span><strong>{html.escape(_("public_step_2"))}</strong></div>'
            f'<div class="side-step"><span class="step-num">3</span><strong>{html.escape(_("public_step_3"))}</strong></div>'
            '</div></div></div>',
            unsafe_allow_html=True,
    )

    if st.session_state.get("bootstrap_missing"):
        st.warning(_("no_admin_configured"))
    if st.session_state.get("bootstrap_error"):
        st.error(_(st.session_state["bootstrap_error"]))

    with st.expander(_("admin_login")):
        show_login_form(_)


def render_admin_view(user, _):
    # Die URL ist die Quelle für die Navigation, auch bei Browser-Zurück.
    event_id = st.query_params.get("event")
    st.session_state.current_event = event_id or None
    if st.session_state.get("current_event") is not None:
        event = DataManager.load_events().get(st.session_state.current_event)
        if event and WichtelLogic.can_user_access_event(event, user.id):
            show_event_details(event, user, _, admin_view=True)
        else:
            st.error(_("event_not_found"))
            st.session_state.current_event = None
            if "event" in st.query_params:
                del st.query_params["event"]
            st.rerun()
        return

    events = WichtelLogic.get_user_events(user.id)
    users = DataManager.load_users()
    started = sum(1 for event in events if event.is_started)

    st.markdown(
        f'<div class="page-heading">{html.escape(_("admin_greeting", name=user.name))}</div>'
        f'<div class="page-subtitle">{html.escape(_("admin_dashboard_subtitle"))}</div>',
        unsafe_allow_html=True,
    )

    metrics = ((_('metric_events'), len(events)), (_('metric_participants'), len(users)), (_('metric_started'), started))
    st.markdown(
        '<div class="metrics-row">' + ''.join(
            f'<div class="metrics-item"><div class="metrics-label">{html.escape(label)}</div>'
            f'<div class="metrics-value">{value}</div></div>' for label, value in metrics
        ) + '</div>', unsafe_allow_html=True,
    )

    tab_events, tab_people, tab_account = st.tabs(
        [_("tab_events"), _("tab_people"), _("tab_account")]
    )

    with tab_events:
        show_event_list(user, _, events=events)
        show_create_event_form(user, _, expanded=not events)

    with tab_people:
        show_user_management(user, _)

    with tab_account:
        show_account_settings(user, _)


def render_participant_view(user, _):
    if not st.session_state.get("current_event"):
        st.warning(_("no_event_for_link"))
        return

    event = DataManager.load_events().get(st.session_state.current_event)
    if event and user.id in event.participant_ids:
        show_event_details(event, user, _, admin_view=False)
    else:
        _clear_auth()
        set_flash("warning", _("event_unavailable_or_not_participant"))
        st.rerun()


def main():
    """Hauptfunktion der App."""
    init_language_support()
    _ = get_translator()
    init_session_state()

    topbar_rendered = False
    hero_rendered = False

    try:
        ensure_admin()
        handle_link_auth(_)

        if st.session_state.pop("bootstrap_created", False):
            set_flash("success", _("admin_created"))

        if st.session_state.get("show_password_change"):
            user = st.session_state.get("temp_user")
            show_topbar(user, _)
            topbar_rendered = True
            hero_rendered = True
            render_flash()
            show_password_change_form(_)
            return

        user = st.session_state.get("user")
        show_topbar(user, _)
        topbar_rendered = True
        if user is None:
            render_hero(_, compact=False)
            hero_rendered = True
        render_flash()

        if user is None:
            render_public_entry(_)
        elif user.is_admin:
            render_admin_view(user, _)
        else:
            render_participant_view(user, _)
    except StorageUnavailableError:
        # Nicht erneut rendern, wenn Topbar/Hero im selben Run schon da sind
        # (sonst doppelte Widget-Keys bzw. doppelter Inhalt).
        if not topbar_rendered:
            show_topbar(None, _)
        if not hero_rendered:
            render_hero(_, compact=False)
        render_storage_error(_)


if __name__ == "__main__":
    main()
