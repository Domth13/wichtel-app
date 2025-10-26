"""
MongoDB-Datenbank-Layer für die Wichtel-App
Ersetzt die JSON-basierten Datenspeicherung
"""
import os
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
import uuid
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv
from dataclasses import asdict

# Type-only imports (nur für Type Checker, nicht zur Laufzeit)
if TYPE_CHECKING:
    from models import User, Event

# Lade Umgebungsvariablen
load_dotenv()


class DatabaseConfig:
    """Datenbank-Konfiguration"""
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "wichtel_app")
    USERS_COLLECTION = "users"
    EVENTS_COLLECTION = "events"


class MongoDB:
    """MongoDB-Verbindungs-Manager"""
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    @classmethod
    def get_client(cls) -> MongoClient:
        """Gibt MongoDB-Client zurück (Singleton)"""
        if cls._client is None:
            cls._client = MongoClient(DatabaseConfig.MONGODB_URI)
        return cls._client
    
    @classmethod
    def get_database(cls) -> Database:
        """Gibt Datenbank zurück"""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[DatabaseConfig.DATABASE_NAME]
        return cls._db
    
    @classmethod
    def get_users_collection(cls) -> Collection:
        """Gibt Users-Collection zurück"""
        db = cls.get_database()
        return db[DatabaseConfig.USERS_COLLECTION]
    
    @classmethod
    def get_events_collection(cls) -> Collection:
        """Gibt Events-Collection zurück"""
        db = cls.get_database()
        return db[DatabaseConfig.EVENTS_COLLECTION]
    
    @classmethod
    def close(cls):
        """Schließt die Datenbankverbindung"""
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None


class MongoDataManager:
    """Datenbank-Manager für MongoDB (ersetzt DataManager)"""
    
    @staticmethod
    def load_users() -> Dict[str, 'User']:
        """Lädt alle Benutzer aus der Datenbank"""
        from models import User
        
        collection = MongoDB.get_users_collection()
        users = {}
        
        for doc in collection.find():
            # Entferne MongoDB's _id
            doc.pop('_id', None)
            user = User.from_dict(doc)
            users[user.id] = user
        
        return users
    
    @staticmethod
    def save_users(users: Dict[str, 'User']):
        """Speichert alle Benutzer in die Datenbank"""
        collection = MongoDB.get_users_collection()
        
        # Lösche alle bestehenden und füge neue ein
        collection.delete_many({})
        
        if users:
            user_docs = [asdict(user) for user in users.values()]
            collection.insert_many(user_docs)
    
    @staticmethod
    def update_user(user: 'User'):
        """Aktualisiert einen einzelnen Benutzer"""
        collection = MongoDB.get_users_collection()
        user_dict = asdict(user)
        
        # Update oder Insert
        collection.update_one(
            {'id': user.id},
            {'$set': user_dict},
            upsert=True
        )
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional['User']:
        """Holt einen Benutzer anhand der ID"""
        from models import User
        
        collection = MongoDB.get_users_collection()
        doc = collection.find_one({'id': user_id})
        
        if doc:
            doc.pop('_id', None)
            return User.from_dict(doc)
        return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional['User']:
        """Sucht Benutzer nach E-Mail"""
        from models import User
        
        collection = MongoDB.get_users_collection()
        doc = collection.find_one({'email': email})
        
        if doc:
            doc.pop('_id', None)
            return User.from_dict(doc)
        return None
    
    @staticmethod
    def authenticate(email: str, password: str) -> Optional['User']:
        """Authentifiziert einen Benutzer"""
        user = MongoDataManager.get_user_by_email(email)
        if user and user.password == password:
            return user
        return None
    
    @staticmethod
    def load_events() -> Dict[str, 'Event']:
        """Lädt alle Events aus der Datenbank"""
        from models import Event
        
        collection = MongoDB.get_events_collection()
        events = {}
        
        for doc in collection.find():
            # Entferne MongoDB's _id
            doc.pop('_id', None)
            event = Event.from_dict(doc)
            events[event.id] = event
        
        return events
    
    @staticmethod
    def save_events(events: Dict[str, 'Event']):
        """Speichert alle Events in die Datenbank"""
        collection = MongoDB.get_events_collection()
        
        # Lösche alle bestehenden und füge neue ein
        collection.delete_many({})
        
        if events:
            event_docs = [event.to_dict() for event in events.values()]
            collection.insert_many(event_docs)
    
    @staticmethod
    def create_event(title: str, creator_id: str, participant_ids: List[str]) -> 'Event':
        """Erstellt ein neues Event"""
        from models import Event
        
        event = Event(
            id=str(uuid.uuid4()),
            title=title,
            created_by=creator_id,
            created_at=datetime.now().isoformat(),
            participant_ids=participant_ids,
            assignments=[]
        )
        
        collection = MongoDB.get_events_collection()
        collection.insert_one(event.to_dict())
        
        return event
    
    @staticmethod
    def update_event(event: 'Event'):
        """Aktualisiert ein Event"""
        collection = MongoDB.get_events_collection()
        
        # Update
        collection.update_one(
            {'id': event.id},
            {'$set': event.to_dict()},
            upsert=True
        )
    
    @staticmethod
    def get_event_by_id(event_id: str) -> Optional['Event']:
        """Holt ein Event anhand der ID"""
        from models import Event
        
        collection = MongoDB.get_events_collection()
        doc = collection.find_one({'id': event_id})
        
        if doc:
            doc.pop('_id', None)
            return Event.from_dict(doc)
        return None
    
    @staticmethod
    def delete_event(event_id: str):
        """Löscht ein Event"""
        collection = MongoDB.get_events_collection()
        collection.delete_one({'id': event_id})
    
    @staticmethod
    def get_events_by_participant(user_id: str) -> List['Event']:
        """Findet alle Events, an denen ein Benutzer teilnimmt"""
        from models import Event
        
        collection = MongoDB.get_events_collection()
        
        # Suche nach Events wo user_id in participant_ids oder created_by ist
        docs = collection.find({
            '$or': [
                {'participant_ids': user_id},
                {'created_by': user_id}
            ]
        })
        
        events = []
        for doc in docs:
            doc.pop('_id', None)
            events.append(Event.from_dict(doc))
        
        # Sortiere nach Erstellungsdatum (neueste zuerst)
        events.sort(key=lambda e: e.created_at, reverse=True)
        
        return events


# Hilfsfunktion für Migration von JSON zu MongoDB
def migrate_json_to_mongodb():
    """
    Migriert Daten von JSON-Files zu MongoDB
    Einmalig ausführen beim Umstieg
    """
    import json
    from models import User, Event
    
    # Importiere config lokal
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import USERS_FILE, EVENTS_FILE
    
    print("🔄 Starte Migration von JSON zu MongoDB...")
    
    # Migriere Users
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            users = {uid: User.from_dict(data) for uid, data in users_data.items()}
            MongoDataManager.save_users(users)
            print(f"✅ {len(users)} Benutzer migriert")
    except FileNotFoundError:
        print("⚠️ users.json nicht gefunden - überspringe User-Migration")
    
    # Migriere Events
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
            events = {eid: Event.from_dict(data) for eid, data in events_data.items()}
            MongoDataManager.save_events(events)
            print(f"✅ {len(events)} Events migriert")
    except FileNotFoundError:
        print("⚠️ events.json nicht gefunden - überspringe Event-Migration")
    
    print("✨ Migration abgeschlossen!")


# Initialisiere Standard-Benutzer wenn DB leer ist
def init_default_users():
    """Erstellt Standard-Benutzer wenn die Datenbank leer ist"""
    from models import User
    
    users = MongoDataManager.load_users()
    
    if not users:
        print("📝 Erstelle Standard-Benutzer...")
        default_users = {
            "user1": User(
                id="user1",
                name="Anna Schmidt",
                email="anna@test.de",
                password="temp123",
                is_admin=True,
                password_changed=False
            ),
            "user2": User(
                id="user2",
                name="Max Müller",
                email="max@test.de",
                password="temp123",
                is_admin=False,
                password_changed=False
            ),
            "user3": User(
                id="user3",
                name="Lisa Weber",
                email="lisa@test.de",
                password="temp123",
                is_admin=False,
                password_changed=False
            ),
            "user4": User(
                id="user4",
                name="Tom Fischer",
                email="tom@test.de",
                password="temp123",
                is_admin=False,
                password_changed=False
            ),
            "user5": User(
                id="user5",
                name="Sarah Klein",
                email="sarah@test.de",
                password="temp123",
                is_admin=False,
                password_changed=False
            )
        }
        MongoDataManager.save_users(default_users)
        print(f"✅ {len(default_users)} Standard-Benutzer erstellt")


if __name__ == "__main__":
    # Test-Skript
    print("🧪 Teste MongoDB-Verbindung...")
    
    try:
        # Teste Verbindung
        client = MongoDB.get_client()
        client.admin.command('ping')
        print("✅ MongoDB-Verbindung erfolgreich!")
        
        # Initialisiere Standard-Benutzer
        init_default_users()
        
        # Zeige Statistiken
        users = MongoDataManager.load_users()
        events = MongoDataManager.load_events()
        print(f"\n📊 Aktuelle Datenbank:")
        print(f"   👥 Benutzer: {len(users)}")
        print(f"   🎄 Events: {len(events)}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        print("\n💡 Stelle sicher, dass MongoDB läuft:")
        print("   - Lokal: mongod")
        print("   - Oder setze MONGODB_URI in .env")
    finally:
        MongoDB.close()