"""
E-Mail-Versand fur die Wichtel-App
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import Event, DataManager
from link_service import LinkAuthService, build_invite_url
from typing import List
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()


class EmailConfig:
    """E-Mail-Konfiguration"""
    # Lade Umgebungsvariablen (optional aus .env)
    # Falls keine Umgebungsvariablen gesetzt sind, bleiben die Platzhalter erhalten
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "deine.email@gmail.com")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "dein_app_passwort")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    APP_URL = os.getenv("APP_URL", "http://localhost:8501")


def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """
    Sendet eine E-Mail uber Gmail
    
    Args:
        to_email: Empfanger E-Mail-Adresse
        subject: E-Mail-Betreff
        body_html: E-Mail-Inhalt (HTML)
    
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        # E-Mail erstellen
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EmailConfig.SENDER_EMAIL
        message["To"] = to_email
        
        # HTML-Teil hinzufugen
        html_part = MIMEText(body_html, "html")
        message.attach(html_part)
        
        # Verbindung zu Gmail herstellen
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
            server.starttls()
            server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)
            server.send_message(message)
        
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand an {to_email}: {e}")
        return False


def create_event_created_email(event_title: str, event_url: str) -> str:
    """Erstellt HTML fur Event-Erstellungs-E-Mail"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>Wichtel-Einladung!</title>
        <link href="https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                font-family: 'Mountains of Christmas', cursive;
                color: #D32F2F; /* Festive Red */
                font-size: 32px;
                margin: 0;
            }}
            .invitation-box {{
                background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%); /* Dark Green to Light Green */
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .invitation-box h2 {{
                font-family: 'Mountains of Christmas', cursive;
                margin: 0;
                font-size: 24px;
            }}
            .button-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .button {{
                background: linear-gradient(135deg, #D32F2F 0%, #E57373 100%); /* Festive Red to Light Red */
                color: white !important;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                display: inline-block;
                font-size: 18px;
            }}
            .footer {{
                font-size: 14px;
                color: #666;
                margin-top: 30px;
                text-align: center;
            }}

            /* Dark Mode Styles */
            @media (prefers-color-scheme: dark) {{
                body {{
                    background-color: #1a1a1a;
                    color: #f4f4f4;
                }}
                .container {{
                    background-color: #2d2d2d;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    border: 1px solid #3a3a3a;
                }}
                .header h1 {{
                    color: #E57373; /* Lighter Red for Dark Mode */
                }}
                .invitation-box {{
                    background: linear-gradient(135deg, #1B5E20 0%, #388E3C 100%); /* Darker Green for Dark Mode */
                }}
                .button {{
                    background: linear-gradient(135deg, #C62828 0%, #D32F2F 100%); /* Darker Red for Dark Mode */
                }}
                .footer {{
                    color: #bbb;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Wichtel-Einladung!</h1>
            </div>
            
            <div class="invitation-box">
                <h2>Du wurdest eingeladen!</h2>
            </div>
            
            <p>Hallo!</p>
            
            <p>Du wurdest zum Wichtel-Event <strong>"{event_title}"</strong> eingeladen!</p>
            
            <p>
                Das Event wurde erstellt und wartet darauf, gestartet zu werden. 
                Du erhältst eine weitere E-Mail, sobald die Wichtel-Zuweisungen erfolgt sind.
            </p>
            
            <div class="button-container">
                <a href="{event_url}" class="button">
                     Zum Event
                </a>
            </div>
            
            <p class="footer">
                Frohe Weihnachten und viel Spaß beim Wichteln!
            </p>
        </div>
    </body>
    </html>
    """


def create_event_started_email(event_title: str, event_url: str) -> str:
    """Erstellt HTML fur Event-Start-E-Mail"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="color-scheme" content="light dark">
        <meta name="supported-color-schemes" content="light dark">
        <title>Dein Wichtel wartet!</title>
        <link href="https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                font-family: 'Mountains of Christmas', cursive;
                color: #2E7D32; /* Dark Green */
                font-size: 32px;
                margin: 0;
            }}
            .assignment-box {{
                background: linear-gradient(135deg, #D32F2F 0%, #E57373 100%); /* Festive Red to Light Red */
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .assignment-box h2 {{
                font-family: 'Mountains of Christmas', cursive;
                margin: 0;
                font-size: 24px;
            }}
            .button-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .button {{
                background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%); /* Dark Green to Light Green */
                color: white !important;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                display: inline-block;
                font-size: 18px;
            }}
            .footer {{
                font-size: 14px;
                color: #666;
                margin-top: 30px;
                text-align: center;
            }}

            /* Dark Mode Styles */
            @media (prefers-color-scheme: dark) {{
                body {{
                    background-color: #1a1a1a;
                    color: #f4f4f4;
                }}
                .container {{
                    background-color: #2d2d2d;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    border: 1px solid #3a3a3a;
                }}
                .header h1 {{
                    color: #4CAF50; /* Lighter Green for Dark Mode */
                }}
                .assignment-box {{
                    background: linear-gradient(135deg, #C62828 0%, #D32F2F 100%); /* Darker Red for Dark Mode */
                }}
                .button {{
                    background: linear-gradient(135deg, #1B5E20 0%, #388E3C 100%); /* Darker Green for Dark Mode */
                }}
                .footer {{
                    color: #bbb;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Los geht's!</h1>
            </div>
            
            <div class="assignment-box">
                <h2>Die Wichtel wurden zugewiesen!</h2>
            </div>
            
            <p>Hallo!</p>
            
            <p>Das Wichtel-Event <strong>"{event_title}"</strong> wurde gestartet!</p>
            
            <p>
                Deine Wichtel-Zuweisung wartet auf dich. Klicke auf den Button unten, 
                um zu erfahren, für wen du ein Geschenk besorgen darfst!
            </p>
            
            <div class="button-container">
                <a href="{event_url}" class="button">
                     Meinen Wichtel zeigen!
                </a>
            </div>
            
            <p class="footer">
                Viel Spaß beim Geschenke besorgen!
            </p>
        </div>
    </body>
    </html>
    """


def send_event_created_emails(event: Event, app_url: str = None) -> List[str]:
    """
    Sendet E-Mails an alle Teilnehmer nach Event-Erstellung
    
    Args:
        event: Das erstellte Event
        app_url: URL zur Streamlit-App (optional, wird aus Config geladen wenn nicht angegeben)
    
    Returns:
        Liste der E-Mail-Adressen, an die erfolgreich versendet wurde
    """
    if app_url is None:
        app_url = EmailConfig.APP_URL
    event = LinkAuthService.ensure_links_for_event(event)
    
    users = DataManager.load_users()
    successful_emails = []
    
    for participant_id in event.participant_ids:
        user = users.get(participant_id)
        if user:
            link = LinkAuthService.get_or_create_link(event, participant_id)
            invite_url = build_invite_url(link.token, app_url)
            subject = f" Einladung zum Wichtel-Event: {event.title}"
            body = create_event_created_email(event.title, invite_url)
            
            if send_email(user.email, subject, body):
                successful_emails.append(user.email)
    
    return successful_emails


def send_event_started_emails(event: Event, app_url: str = None) -> List[str]:
    """
    Sendet E-Mails an alle Teilnehmer nach Event-Start
    
    Args:
        event: Das gestartete Event
        app_url: URL zur Streamlit-App (optional, wird aus Config geladen wenn nicht angegeben)
    
    Returns:
        Liste der E-Mail-Adressen, an die erfolgreich versendet wurde
    """
    if app_url is None:
        app_url = EmailConfig.APP_URL
    
    event = LinkAuthService.ensure_links_for_event(event)
    users = DataManager.load_users()
    successful_emails = []
    
    for participant_id in event.participant_ids:
        user = users.get(participant_id)
        if user:
            link = LinkAuthService.get_or_create_link(event, participant_id)
            invite_url = build_invite_url(link.token, app_url)
            subject = f" Dein Wichtel wartet auf dich: {event.title}"
            body = create_event_started_email(event.title, invite_url)
            
            if send_email(user.email, subject, body):
                successful_emails.append(user.email)
    
    return successful_emails
