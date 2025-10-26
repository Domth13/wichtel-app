"""
E-Mail-Versand für die Wichtel-App
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import Event, DataManager
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
    Sendet eine E-Mail über Gmail
    
    Args:
        to_email: Empfänger E-Mail-Adresse
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
        
        # HTML-Teil hinzufügen
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
    """Erstellt HTML für Event-Erstellungs-E-Mail"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #667eea; font-size: 32px;">🎄 Wichtel-Einladung! 🎅</h1>
                </div>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">Du wurdest eingeladen!</h2>
                </div>
                
                <p style="font-size: 16px;">
                    Hallo! 👋
                </p>
                
                <p style="font-size: 16px;">
                    Du wurdest zum Wichtel-Event <strong>"{event_title}"</strong> eingeladen!
                </p>
                
                <p style="font-size: 16px;">
                    Das Event wurde erstellt und wartet darauf, gestartet zu werden. 
                    Du erhältst eine weitere E-Mail, sobald die Wichtel-Zuweisungen erfolgt sind.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{event_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; padding: 15px 30px; text-decoration: none;
                              border-radius: 25px; font-weight: bold; display: inline-block;">
                        🎁 Zum Event
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Frohe Weihnachten und viel Spaß beim Wichteln! ✨
                </p>
            </div>
        </body>
    </html>
    """


def create_event_started_email(event_title: str, event_url: str) -> str:
    """Erstellt HTML für Event-Start-E-Mail"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 80px; animation: bounce 1s infinite;">🎁</div>
                    <h1 style="color: #667eea; font-size: 32px;">Los geht's! 🎅</h1>
                </div>
                
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">Die Wichtel wurden zugewiesen!</h2>
                </div>
                
                <p style="font-size: 16px;">
                    Hallo! 👋
                </p>
                
                <p style="font-size: 16px;">
                    Das Wichtel-Event <strong>"{event_title}"</strong> wurde gestartet!
                </p>
                
                <p style="font-size: 16px;">
                    Deine Wichtel-Zuweisung wartet auf dich. Klicke auf den Button unten, 
                    um zu erfahren, für wen du ein Geschenk besorgen darfst! 🎁
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{event_url}" 
                       style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                              color: white; padding: 15px 30px; text-decoration: none;
                              border-radius: 25px; font-weight: bold; display: inline-block;
                              font-size: 18px;">
                        🎅 Meinen Wichtel zeigen!
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Viel Spaß beim Geschenke besorgen! 🎄✨
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
    
    users = DataManager.load_users()
    successful_emails = []
    
    for participant_id in event.participant_ids:
        user = users.get(participant_id)
        if user:
            subject = f"🎄 Einladung zum Wichtel-Event: {event.title}"
            body = create_event_created_email(event.title, app_url)
            
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
    
    users = DataManager.load_users()
    successful_emails = []
    
    for participant_id in event.participant_ids:
        user = users.get(participant_id)
        if user:
            subject = f"🎁 Dein Wichtel wartet auf dich: {event.title}"
            body = create_event_started_email(event.title, app_url)
            
            if send_email(user.email, subject, body):
                successful_emails.append(user.email)
    
    return successful_emails