"""
Konfigurationsdatei für die Wichtel-App
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Dateipfade (absolut, damit die App unabhängig vom Arbeitsverzeichnis läuft)
USERS_FILE = str(BASE_DIR / "users.json")
EVENTS_FILE = str(BASE_DIR / "events.json")

# Session State Keys
SESSION_USER = "user"
SESSION_EVENT = "current_event"
SESSION_VIEW = "view"

# Views
VIEW_LOGIN = "login"
VIEW_ADMIN = "admin"
VIEW_PARTICIPANT = "participant"
VIEW_EVENT_REVEAL = "reveal"

# App Einstellungen
APP_TITLE = "🎄 Wichtel App 🎅"
APP_ICON = "🎁"
