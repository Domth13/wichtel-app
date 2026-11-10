"""
MongoDB-Datenbank-Layer für die Wichtel-App.
"""
import logging
import os
import threading
import uuid
from dataclasses import asdict
from datetime import datetime
from functools import wraps
from typing import TYPE_CHECKING, Dict, List, Optional

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from security import hash_password, is_password_hash, verify_password
from storage_cache import StorageUnavailableError, cached, invalidate

if TYPE_CHECKING:
    from models import Event, User

load_dotenv()
logger = logging.getLogger(__name__)

_CACHE_TTL = 3.0
_USERS_CACHE_KEY = "mongo_users"
_EVENTS_CACHE_KEY = "mongo_events"


class DatabaseConfig:
    """Datenbank-Konfiguration"""
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "wichtel_app")
    USERS_COLLECTION = "users"
    EVENTS_COLLECTION = "events"


class MongoDB:
    """MongoDB-Verbindungs-Manager (Singleton pro Prozess)."""
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _client_lock = threading.Lock()

    @classmethod
    def get_client(cls) -> MongoClient:
        with cls._client_lock:
            if cls._client is None:
                cls._client = MongoClient(
                    DatabaseConfig.MONGODB_URI,
                    serverSelectionTimeoutMS=6000,
                    connectTimeoutMS=6000,
                    socketTimeoutMS=20000,
                    retryWrites=True,
                    appname="wichtel-app",
                )
        return cls._client

    @classmethod
    def get_database(cls) -> Database:
        if cls._db is None:
            cls._db = cls.get_client()[DatabaseConfig.DATABASE_NAME]
        return cls._db

    @classmethod
    def get_users_collection(cls) -> Collection:
        return cls.get_database()[DatabaseConfig.USERS_COLLECTION]

    @classmethod
    def get_events_collection(cls) -> Collection:
        return cls.get_database()[DatabaseConfig.EVENTS_COLLECTION]

    @classmethod
    def close(cls):
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None


def _guard(func):
    """Wandelt MongoDB-Fehler in eine verständliche App-Meldung um."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PyMongoError as exc:
            logger.error("MongoDB-Fehler: %s", exc)
            raise StorageUnavailableError(
                "Die Datenbank ist momentan nicht erreichbar."
            ) from exc
    return wrapper


class MongoDataManager:
    """Datenbank-Manager für MongoDB."""

    # ---------- Benutzer ----------

    @staticmethod
    @_guard
    def load_users() -> Dict[str, "User"]:
        from models import User

        def _load():
            collection = MongoDB.get_users_collection()
            users = {}
            for doc in collection.find():
                doc.pop("_id", None)
                user = User.from_dict(doc)
                users[user.id] = user
            return users

        return cached(_USERS_CACHE_KEY, _load, _CACHE_TTL)

    @staticmethod
    @_guard
    def save_users(users: Dict[str, "User"]):
        collection = MongoDB.get_users_collection()
        incoming_ids = set(users.keys())
        existing_ids = set(collection.distinct("id"))

        removed = existing_ids - incoming_ids
        if removed:
            collection.delete_many({"id": {"$in": list(removed)}})

        if users:
            collection.bulk_write(
                [
                    UpdateOne({"id": user.id}, {"$set": asdict(user)}, upsert=True)
                    for user in users.values()
                ]
            )
        invalidate(_USERS_CACHE_KEY)

    @staticmethod
    @_guard
    def update_user(user: "User"):
        collection = MongoDB.get_users_collection()
        collection.update_one(
            {"id": user.id},
            {"$set": asdict(user)},
            upsert=True,
        )
        invalidate(_USERS_CACHE_KEY)

    @staticmethod
    @_guard
    def create_user(
        name: str,
        email: str,
        password: Optional[str] = None,
        is_admin: bool = False,
    ) -> "User":
        import secrets

        from models import User

        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name:
            raise ValueError("name_required")
        if not email or "@" not in email:
            raise ValueError("email_invalid")
        if MongoDataManager.get_user_by_email(email):
            raise ValueError("email_exists")

        user = User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=hash_password(password or secrets.token_urlsafe(24)),
            is_admin=bool(is_admin),
            password_changed=False,
        )
        collection = MongoDB.get_users_collection()
        collection.insert_one(asdict(user))
        invalidate(_USERS_CACHE_KEY)
        return user

    @staticmethod
    @_guard
    def get_user_by_email(email: str) -> Optional["User"]:
        target = (email or "").strip().lower()
        if not target:
            return None
        for user in MongoDataManager.load_users().values():
            if (user.email or "").strip().lower() == target:
                return user
        return None

    @staticmethod
    @_guard
    def authenticate(email: str, password: str) -> Optional["User"]:
        user = MongoDataManager.get_user_by_email(email)
        if not user or not verify_password(password, user.password):
            return None
        if not is_password_hash(user.password):
            user.password = hash_password(password)
            MongoDataManager.update_user(user)
        return user

    # ---------- Events ----------

    @staticmethod
    @_guard
    def load_events() -> Dict[str, "Event"]:
        from models import Event

        def _load():
            collection = MongoDB.get_events_collection()
            events = {}
            for doc in collection.find():
                doc.pop("_id", None)
                event = Event.from_dict(doc)
                events[event.id] = event
            return events

        return cached(_EVENTS_CACHE_KEY, _load, _CACHE_TTL)

    @staticmethod
    @_guard
    def save_events(events: Dict[str, "Event"]):
        collection = MongoDB.get_events_collection()
        incoming_ids = set(events.keys())
        existing_ids = set(collection.distinct("id"))

        removed = existing_ids - incoming_ids
        if removed:
            collection.delete_many({"id": {"$in": list(removed)}})

        if events:
            collection.bulk_write(
                [
                    UpdateOne(
                        {"id": event.id},
                        {"$set": event.to_dict()},
                        upsert=True,
                    )
                    for event in events.values()
                ]
            )
        invalidate(_EVENTS_CACHE_KEY)

    @staticmethod
    @_guard
    def create_event(
        title: str,
        creator_id: str,
        participant_ids: List[str],
        gift_value: str = "",
        event_date: str = "",
        location: str = "",
        description: str = "",
    ) -> "Event":
        from models import Event

        event = Event(
            id=str(uuid.uuid4()),
            title=(title or "").strip(),
            created_by=creator_id,
            created_at=datetime.now().isoformat(),
            participant_ids=list(participant_ids),
            assignments=[],
            gift_value=(gift_value or "").strip(),
            event_date=(event_date or "").strip(),
            location=(location or "").strip(),
            description=(description or "").strip(),
        )
        collection = MongoDB.get_events_collection()
        collection.insert_one(event.to_dict())
        invalidate(_EVENTS_CACHE_KEY)
        return event

    @staticmethod
    @_guard
    def update_event(event: "Event"):
        collection = MongoDB.get_events_collection()
        collection.update_one(
            {"id": event.id},
            {"$set": event.to_dict()},
            upsert=True,
        )
        invalidate(_EVENTS_CACHE_KEY)

    @staticmethod
    @_guard
    def update_event_fields(event: "Event", fields):
        values = event.to_dict()
        result = MongoDB.get_events_collection().update_one(
            {"id": event.id}, {"$set": {field: values[field] for field in fields}}
        )
        if not result.matched_count:
            raise ValueError("event_not_found")
        invalidate(_EVENTS_CACHE_KEY)

    @staticmethod
    @_guard
    def mark_revealed(event_id: str, user_id: str) -> bool:
        collection = MongoDB.get_events_collection()
        result = collection.update_one(
            {"id": event_id, "assignments.giver_id": user_id},
            {"$set": {"assignments.$.revealed": True}},
        )
        invalidate(_EVENTS_CACHE_KEY)
        return result.matched_count > 0

    @staticmethod
    @_guard
    def delete_event(event_id: str):
        collection = MongoDB.get_events_collection()
        collection.delete_one({"id": event_id})
        invalidate(_EVENTS_CACHE_KEY)

    @staticmethod
    @_guard
    def get_event_by_id(event_id: str) -> Optional["Event"]:
        from models import Event

        collection = MongoDB.get_events_collection()
        doc = collection.find_one({"id": event_id})
        if not doc:
            return None
        doc.pop("_id", None)
        return Event.from_dict(doc)

    @staticmethod
    @_guard
    def get_events_by_participant(user_id: str) -> List["Event"]:
        from models import Event

        collection = MongoDB.get_events_collection()
        docs = collection.find(
            {"$or": [{"participant_ids": user_id}, {"created_by": user_id}]}
        )
        events = []
        for doc in docs:
            doc.pop("_id", None)
            events.append(Event.from_dict(doc))
        events.sort(key=lambda item: item.created_at, reverse=True)
        return events


def migrate_json_to_mongodb():
    """Einmalige Migration von JSON-Dateien nach MongoDB."""
    import json

    from config import EVENTS_FILE, USERS_FILE
    from models import Event, User

    print("Starte Migration von JSON nach MongoDB...")

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as fh:
            users_data = json.load(fh)
        users = {uid: User.from_dict(data) for uid, data in users_data.items()}
        for user in users.values():
            if not is_password_hash(user.password):
                user.password = hash_password(user.password)
        MongoDataManager.save_users(users)
        print(f"{len(users)} Benutzer migriert")
    except FileNotFoundError:
        print("users.json nicht gefunden - überspringe Benutzer")

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as fh:
            events_data = json.load(fh)
        events = {eid: Event.from_dict(data) for eid, data in events_data.items()}
        MongoDataManager.save_events(events)
        print(f"{len(events)} Events migriert")
    except FileNotFoundError:
        print("events.json nicht gefunden - überspringe Events")

    print("Migration abgeschlossen.")


if __name__ == "__main__":
    import sys

    if "--migrate" in sys.argv:
        migrate_json_to_mongodb()
        raise SystemExit(0)

    print("Teste MongoDB-Verbindung...")
    try:
        client = MongoDB.get_client()
        client.admin.command("ping")
        print("MongoDB-Verbindung erfolgreich.")

        users = MongoDataManager.load_users()
        events = MongoDataManager.load_events()
        print(f"Benutzer: {len(users)}")
        print(f"Events: {len(events)}")
    except Exception as exc:
        print(f"Fehler: {exc}")
        print("Prüfe MONGODB_URI und ob die Datenbank erreichbar ist.")
    finally:
        MongoDB.close()
