"""
Datenmodelle und Speicherung für die Wichtel-App.

Unterstützt JSON-Dateien (lokal/klein) und MongoDB (empfohlen für Cloud).
Passwörter werden gehasht; alte Klartext-Passwörter werden beim Login migriert.
"""
import json
import logging
import os
import secrets
import threading
import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import EVENTS_FILE, USERS_FILE
from security import hash_password, is_password_hash, verify_password
from storage_cache import StorageUnavailableError, cached, invalidate

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None

logger = logging.getLogger(__name__)

_JSON_LOCK = threading.RLock()
_CACHE_TTL = 3.0


def _apply_env_from_mapping(mapping, prefix=""):
    for key, value in mapping.items():
        env_key = f"{prefix}{key}" if not prefix else f"{prefix}{key}".upper()
        if isinstance(value, dict):
            _apply_env_from_mapping(value, prefix=f"{env_key}_")
        elif isinstance(value, (str, int, float, bool)):
            os.environ.setdefault(str(env_key), str(value))


def _load_streamlit_secrets():
    """Liest Secrets direkt über st.secrets (lokal und auf Streamlit Cloud)."""
    try:
        import streamlit as st
        secrets_obj = getattr(st, "secrets", None)
        if secrets_obj is None:
            return False
        # load_if_toml_exists() unterdrückt Fehlermeldungen, wenn (lokal)
        # keine Secrets-Datei vorhanden ist.
        if hasattr(secrets_obj, "load_if_toml_exists"):
            if not secrets_obj.load_if_toml_exists():
                return False
        extracted = {key: secrets_obj[key] for key in secrets_obj}
        if not extracted:
            return False
        _apply_env_from_mapping(extracted)
        return True
    except Exception:
        return False


def _load_local_secrets():
    secrets_file = Path("secrets.toml")
    if not secrets_file.exists() or tomllib is None:
        return False
    try:
        with secrets_file.open("rb") as fh:
            data = tomllib.load(fh)
        _apply_env_from_mapping(data)
        return True
    except Exception:
        return False


def _load_dotenv_file():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


_load_streamlit_secrets()
_load_local_secrets()
_load_dotenv_file()


def _filter_fields(cls, data: dict) -> dict:
    allowed = {item.name for item in fields(cls)}
    return {key: value for key, value in data.items() if key in allowed}


@dataclass
class User:
    """Benutzer-Modell. Das Feld password enthält einen Hash (oder Alt-Klartext)."""
    id: str
    name: str
    email: str
    password: str
    is_admin: bool = False
    password_changed: bool = False

    @classmethod
    def from_dict(cls, data: dict):
        data = _filter_fields(cls, data.copy())
        data.setdefault("is_admin", False)
        data.setdefault("password_changed", False)
        return cls(**data)


@dataclass
class Assignment:
    """Wichtel-Zuweisung"""
    giver_id: str
    receiver_id: str
    revealed: bool = False

    @classmethod
    def from_dict(cls, data: dict):
        data = _filter_fields(cls, data.copy())
        data.setdefault("revealed", False)
        return cls(**data)


@dataclass
class AccessLink:
    """Einladungs-Link für Teilnehmer"""
    token: str
    user_id: str
    created_at: str
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict):
        data = _filter_fields(cls, data.copy())
        data.setdefault("disabled", False)
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
    access_links: List[AccessLink] = field(default_factory=list)
    is_started: bool = False
    gift_value: str = ""
    event_date: str = ""
    location: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        data.pop("is_revealed", None)
        data = _filter_fields(cls, data)

        data["assignments"] = [
            Assignment.from_dict(item) for item in data.get("assignments", [])
        ]
        data["access_links"] = [
            AccessLink.from_dict(item) for item in data.get("access_links", [])
        ]
        data.setdefault("gift_value", "")
        data.setdefault("event_date", "")
        data.setdefault("location", "")
        data.setdefault("description", "")
        data.setdefault("is_started", False)
        return cls(**data)

    def to_dict(self):
        return asdict(self)


def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise StorageUnavailableError(f"Ungültiges Datenformat in {path}")
        return data
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise StorageUnavailableError(
            f"Datendatei {path} ist beschädigt. Bitte aus Backup wiederherstellen."
        ) from exc
    except OSError as exc:
        raise StorageUnavailableError(
            f"Datendatei {path} konnte nicht gelesen werden."
        ) from exc


def _write_json(path: str, data: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    except OSError as exc:
        raise StorageUnavailableError(
            f"Datendatei {target} konnte nicht geschrieben werden."
        ) from exc
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


class JSONDataManager:
    """Verwaltet Benutzer und Events in JSON-Dateien."""

    @staticmethod
    def _users_key() -> str:
        return f"json_users:{USERS_FILE}"

    @staticmethod
    def _events_key() -> str:
        return f"json_events:{EVENTS_FILE}"

    # ---------- Benutzer ----------

    @staticmethod
    def load_users() -> Dict[str, User]:
        def _load():
            data = _read_json(USERS_FILE)
            return {
                uid: User.from_dict(user_data)
                for uid, user_data in data.items()
                if isinstance(user_data, dict)
            }

        return cached(JSONDataManager._users_key(), _load, _CACHE_TTL)

    @staticmethod
    def save_users(users: Dict[str, User]):
        _write_json(USERS_FILE, {uid: asdict(user) for uid, user in users.items()})
        invalidate(JSONDataManager._users_key())

    @staticmethod
    def update_user(user: User):
        with _JSON_LOCK:
            invalidate(JSONDataManager._users_key())
            users = JSONDataManager.load_users()
            users[user.id] = user
            JSONDataManager.save_users(users)

    @staticmethod
    def create_user(
        name: str,
        email: str,
        password: Optional[str] = None,
        is_admin: bool = False,
    ) -> User:
        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name:
            raise ValueError("name_required")
        if not email or "@" not in email:
            raise ValueError("email_invalid")

        with _JSON_LOCK:
            invalidate(JSONDataManager._users_key())
            users = JSONDataManager.load_users()
            if any((item.email or "").strip().lower() == email for item in users.values()):
                raise ValueError("email_exists")

            user = User(
                id=str(uuid.uuid4()),
                name=name,
                email=email,
                password=hash_password(password or secrets.token_urlsafe(24)),
                is_admin=bool(is_admin),
                password_changed=False,
            )
            users[user.id] = user
            JSONDataManager.save_users(users)
            return user

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        target = (email or "").strip().lower()
        if not target:
            return None
        for user in JSONDataManager.load_users().values():
            if (user.email or "").strip().lower() == target:
                return user
        return None

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[User]:
        user = JSONDataManager.get_user_by_email(email)
        if not user or not verify_password(password, user.password):
            return None

        # Altbestand: Klartext-Passwort beim ersten erfolgreichen Login ersetzen.
        if not is_password_hash(user.password):
            user.password = hash_password(password)
            JSONDataManager.update_user(user)
        return user

    # ---------- Events ----------

    @staticmethod
    def load_events() -> Dict[str, Event]:
        def _load():
            data = _read_json(EVENTS_FILE)
            return {
                eid: Event.from_dict(event_data)
                for eid, event_data in data.items()
                if isinstance(event_data, dict)
            }

        return cached(JSONDataManager._events_key(), _load, _CACHE_TTL)

    @staticmethod
    def save_events(events: Dict[str, Event]):
        _write_json(EVENTS_FILE, {eid: event.to_dict() for eid, event in events.items()})
        invalidate(JSONDataManager._events_key())

    @staticmethod
    def create_event(
        title: str,
        creator_id: str,
        participant_ids: List[str],
        gift_value: str = "",
        event_date: str = "",
        location: str = "",
        description: str = "",
    ) -> Event:
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
        with _JSON_LOCK:
            invalidate(JSONDataManager._events_key())
            events = JSONDataManager.load_events()
            events[event.id] = event
            JSONDataManager.save_events(events)
        return event

    @staticmethod
    def update_event(event: Event):
        with _JSON_LOCK:
            invalidate(JSONDataManager._events_key())
            events = JSONDataManager.load_events()
            events[event.id] = event
            JSONDataManager.save_events(events)

    @staticmethod
    def update_event_fields(event: Event, fields):
        """Ändert nur die angegebenen Felder und erhält parallele Änderungen."""
        with _JSON_LOCK:
            invalidate(JSONDataManager._events_key())
            events = JSONDataManager.load_events()
            current = events.get(event.id)
            if current is None:
                raise ValueError("event_not_found")
            values = current.to_dict()
            updated = event.to_dict()
            for field in fields:
                values[field] = updated[field]
            events[event.id] = Event.from_dict(values)
            JSONDataManager.save_events(events)

    @staticmethod
    def mark_revealed(event_id: str, user_id: str) -> bool:
        with _JSON_LOCK:
            invalidate(JSONDataManager._events_key())
            events = JSONDataManager.load_events()
            event = events.get(event_id)
            if not event:
                return False
            changed = False
            for assignment in event.assignments:
                if assignment.giver_id == user_id:
                    assignment.revealed = True
                    changed = True
                    break
            if changed:
                JSONDataManager.save_events(events)
            return changed

    @staticmethod
    def delete_event(event_id: str):
        with _JSON_LOCK:
            invalidate(JSONDataManager._events_key())
            events = JSONDataManager.load_events()
            if event_id in events:
                del events[event_id]
                JSONDataManager.save_events(events)

    @staticmethod
    def get_event_by_id(event_id: str) -> Optional[Event]:
        return JSONDataManager.load_events().get(event_id)

    @staticmethod
    def get_events_by_participant(user_id: str) -> List[Event]:
        events = JSONDataManager.load_events().values()
        user_events = [
            event
            for event in events
            if user_id in event.participant_ids or user_id == event.created_by
        ]
        return sorted(user_events, key=lambda item: item.created_at, reverse=True)


# Bestimme, welchen DataManager wir verwenden.
USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() == "true"

if USE_MONGODB:
    try:
        from database import MongoDataManager

        DataManager = MongoDataManager
        logger.info("Verwende MongoDB als Datenbank")
    except ImportError as exc:
        logger.error("MongoDB-Import fehlgeschlagen: %s", exc)
        DataManager = JSONDataManager
else:
    DataManager = JSONDataManager
    logger.info("Verwende JSON-Dateien als Datenbank")
