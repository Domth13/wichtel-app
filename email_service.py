"""
E-Mail-Versand für die Wichtel-App.
"""
import html
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import List, Optional, Tuple

from dotenv import load_dotenv

from email_templates import render_event_email
from language import TRANSLATIONS
from link_service import LinkAuthService, build_invite_url
from models import DataManager, Event

load_dotenv()
logger = logging.getLogger(__name__)


class EmailConfig:
    """E-Mail-Konfiguration aus Umgebungsvariablen / Streamlit-Secrets."""
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "deine.email@gmail.com")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "dein_app_passwort")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    try:
        SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        SMTP_PORT = 587
    APP_URL = os.getenv("APP_URL", "http://localhost:8501")


def email_configured() -> bool:
    """True, wenn echte SMTP-Zugangsdaten hinterlegt sind."""
    return bool(
        EmailConfig.SENDER_EMAIL
        and EmailConfig.SENDER_PASSWORD
        and "deine.email" not in EmailConfig.SENDER_EMAIL
        and "dein_app_passwort" not in EmailConfig.SENDER_PASSWORD
    )


def _translations(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["de"])


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    server: Optional[smtplib.SMTP] = None,
) -> bool:
    """Sendet eine E-Mail. Fehler werden geloggt, nicht an die UI geworfen."""
    own_connection = server is None
    smtp = server
    try:
        message = MIMEMultipart("alternative")
        # Zeilenumbrüche im Betreff verhindern Header-Injection.
        message["Subject"] = " ".join(str(subject).splitlines())
        message["From"] = EmailConfig.SENDER_EMAIL
        message["To"] = to_email
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid()
        message.attach(MIMEText(body_html, "html", "utf-8"))

        if own_connection:
            smtp = smtplib.SMTP(
                EmailConfig.SMTP_SERVER,
                EmailConfig.SMTP_PORT,
                timeout=15,
            )
            smtp.starttls()
            smtp.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)

        smtp.send_message(message)
        return True
    except Exception as exc:
        logger.warning("E-Mail an %s fehlgeschlagen: %s", to_email, exc)
        return False
    finally:
        if own_connection and smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass


def _send_bulk(items: List[Tuple[str, str, str]]) -> dict:
    """Sendet mehrere Mails über eine SMTP-Verbindung."""
    if not items:
        return {"sent": [], "failed": [], "skipped": False}
    if not email_configured():
        return {
            "sent": [],
            "failed": [to for to, _subject, _body in items],
            "skipped": True,
        }

    sent: List[str] = []
    failed: List[str] = []
    smtp = None
    try:
        smtp = smtplib.SMTP(
            EmailConfig.SMTP_SERVER,
            EmailConfig.SMTP_PORT,
            timeout=15,
        )
        smtp.starttls()
        smtp.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)

        for to_email, subject, body_html in items:
            if send_email(to_email, subject, body_html, server=smtp):
                sent.append(to_email)
            else:
                failed.append(to_email)
    except Exception as exc:
        logger.warning("SMTP-Verbindung fehlgeschlagen: %s", exc)
        for to_email, _subject, _body in items:
            if to_email not in sent and to_email not in failed:
                failed.append(to_email)
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass

    return {"sent": sent, "failed": failed, "skipped": False}


def _create_event_email(event_title: str, event_url: str, lang: str, kind: str) -> str:
    """Erstellt Einladungs- und Startmails im gemeinsamen Layout."""
    t = _translations(lang)
    prefix = f"email_{kind}_"
    event_text = t[prefix + "body_event"].format(
        event_title=html.escape(event_title or "", quote=True)
    )
    detail_key = "body_waiting" if kind == "invite" else "body_assignment"
    return render_event_email(
        lang=lang,
        heading=t[prefix + "heading"],
        subheading=t[prefix + "subheading"],
        hello=t[prefix + "body_hello"],
        event_text=event_text,
        detail=t[prefix + detail_key],
        button=t[prefix + "button"],
        footer=t[prefix + "footer"],
        url=event_url,
    )


def create_event_created_email(event_title: str, event_url: str, lang: str = "de") -> str:
    """HTML für die Einladungs-E-Mail."""
    return _create_event_email(event_title, event_url, lang, "invite")


def create_event_started_email(event_title: str, event_url: str, lang: str = "de") -> str:
    """HTML für die Start-E-Mail."""
    return _create_event_email(event_title, event_url, lang, "started")


def _build_invites(event: Event, lang: str) -> List[Tuple[str, str, str]]:
    t = _translations(lang)
    event = LinkAuthService.ensure_links_for_event(event)
    users = DataManager.load_users()
    items = []
    for participant_id in event.participant_ids:
        user = users.get(participant_id)
        if not user:
            continue
        link = LinkAuthService.get_link_for_user(event, participant_id)
        if link is None:
            continue
        invite_url = build_invite_url(link.token, EmailConfig.APP_URL)
        subject = t["email_invite_subject"].format(event_title=event.title)
        body = create_event_created_email(event.title, invite_url, lang=lang)
        items.append((user.email, subject, body))
    return items


def send_event_created_emails(event: Event, lang: str = "de") -> dict:
    """Sendet Einladungen an alle Teilnehmer; liefert eine Ergebnisübersicht."""
    return _send_bulk(_build_invites(event, lang))


def send_event_started_emails(event: Event, lang: str = "de") -> dict:
    """Sendet die Startmails an alle Teilnehmer; liefert eine Ergebnisübersicht."""
    t = _translations(lang)
    event = LinkAuthService.ensure_links_for_event(event)
    users = DataManager.load_users()
    items = []
    for participant_id in event.participant_ids:
        user = users.get(participant_id)
        if not user:
            continue
        link = LinkAuthService.get_link_for_user(event, participant_id)
        if link is None:
            continue
        invite_url = build_invite_url(link.token, EmailConfig.APP_URL)
        subject = t["email_started_subject"].format(event_title=event.title)
        body = create_event_started_email(event.title, invite_url, lang=lang)
        items.append((user.email, subject, body))
    return _send_bulk(items)
