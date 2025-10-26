"""
Datenmodelle für die Wichtel-App
Unterstützt sowohl MongoDB als auch JSON-Files
"""
import json
import uuid
import os
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from config import USERS_FILE, EVENTS_FILE

# WICHTIG: Lade .env ZUERST
from dotenv import load_dotenv
load_dotenv()


@dataclass
class User:
    """Benutzer-Modell"""
    id: str
    name: str
    email: str
    password: str
    is_admin: bool = False
    password_changed: bool = False
    
    @classmethod
    def from_dict(cls, data: dict):
        # Setze Standardwerte für neue Felder, falls sie fehlen
        data = data.copy()
        if 'is_admin' not in data:
            data['is_admin'] = False
        if 'password_changed' not in data:
            data['password_changed'] = False
        return cls(**data)


@dataclass
class Assignment:
    """Wichtel-Zuweisung"""
    giver_id: str
    receiver_id: str
    revealed: bool = False
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class Event:
    """Wichtel-Event"""
    id: str
    title: str
    created_by: str
    created_at: str
    participant_ids: List[str]
    assignments: List[Assignment]
    is_started: bool = False
    
    @classmethod
    def from_dict(cls, data: dict):
        # Entferne veraltete Felder für Abwärtskompatibilität
        data = data.copy()
        data.pop('is_revealed', None)
        
        data['assignments'] = [Assignment.from_dict(a) for a in data.get('assignments', [])]
        return cls(**data)
    
    def to_dict(self):
        result = asdict(self)
        result['assignments'] = [asdict(a) for a in self.assignments]
        return result


# JSON-basierter DataManager (Fallback)
class JSONDataManager:
    """Verwaltet das Laden und Speichern von Daten (JSON-basiert)"""
    
    @staticmethod
    def load_users() -> Dict[str, User]:
        """Lädt Benutzer aus JSON-Datei"""
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {uid: User.from_dict(user_data) for uid, user_data in data.items()}
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def save_users(users: Dict[str, User]):
        """Speichert Benutzer in JSON-Datei"""
        data = {uid: asdict(user) for uid, user in users.items()}
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def update_user(user: User):
        """Aktualisiert einen Benutzer"""
        users = JSONDataManager.load_users()
        users[user.id] = user
        JSONDataManager.save_users(users)
    
    @staticmethod
    def create_event(title: str, creator_id: str, participant_ids: List[str]) -> Event:
        """Erstellt ein neues Event"""
        event = Event(
            id=str(uuid.uuid4()),
            title=title,
            created_by=creator_id,
            created_at=datetime.now().isoformat(),
            participant_ids=participant_ids,
            assignments=[]
        )
        events = JSONDataManager.load_events()
        events[event.id] = event
        JSONDataManager.save_events(events)
        return event
    
    @staticmethod
    def delete_event(event_id: str):
        """Löscht ein Event"""
        events = JSONDataManager.load_events()
        if event_id in events:
            del events[event_id]
            JSONDataManager.save_events(events)
    
    @staticmethod
    def load_events() -> Dict[str, Event]:
        """Lädt Events aus JSON-Datei"""
        try:
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {eid: Event.from_dict(event_data) for eid, event_data in data.items()}
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def save_events(events: Dict[str, Event]):
        """Speichert Events in JSON-Datei"""
        data = {eid: event.to_dict() for eid, event in events.items()}
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Sucht Benutzer nach E-Mail"""
        users = JSONDataManager.load_users()
        for user in users.values():
            if user.email == email:
                return user
        return None
    
    @staticmethod
    def authenticate(email: str, password: str) -> Optional[User]:
        """Authentifiziert einen Benutzer"""
        user = JSONDataManager.get_user_by_email(email)
        if user and user.password == password:
            return user
        return None


# Bestimme welchen DataManager wir verwenden
USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() == "true"

if USE_MONGODB:
    # Verwende MongoDB
    try:
        from database import MongoDataManager
        DataManager = MongoDataManager
        print("✅ Verwende MongoDB als Datenbank")
    except ImportError as e:
        print(f"⚠️ MongoDB-Import fehlgeschlagen: {e}")
        print("📁 Fallback auf JSON-Files")
        DataManager = JSONDataManager
else:
    # Verwende JSON-Files (Standard)
    DataManager = JSONDataManager
    print("📁 Verwende JSON-Files als Datenbank")