"""
Service fr Magic-Link Authentifizierung der Teilnehmer
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple

from models import Event, AccessLink, DataManager


def build_invite_url(token: str, base_url: Optional[str] = None) -> str:
    """Baut eine URL fuer Einladungslinks"""
    base = (base_url or os.getenv("APP_URL") or "http://localhost:8501").rstrip("/")
    return f"{base}?token={token}"



class LinkAuthService:
    """Verwaltet Einladungs-Links pro Event/Teilnehmer"""
    TOKEN_PREFIX = "wtl_"

    @staticmethod
    def _generate_token() -> str:
        return f"{LinkAuthService.TOKEN_PREFIX}{uuid.uuid4().hex}"

    @staticmethod
    def ensure_links_for_event(event: Event) -> Event:
        """
        Stellt sicher, dass alle Teilnehmer einen Link haben
        """
        changed = False
        existing_user_ids = {link.user_id for link in event.access_links if not link.disabled}

        for participant_id in event.participant_ids:
            if participant_id not in existing_user_ids:
                event.access_links.append(
                    AccessLink(
                        token=LinkAuthService._generate_token(),
                        user_id=participant_id,
                        created_at=datetime.now().isoformat(),
                        disabled=False
                    )
                )
                changed = True

        if changed:
            LinkAuthService._persist_event(event)

        return event

    @staticmethod
    def get_link_for_user(event: Event, user_id: str) -> Optional[AccessLink]:
        for link in event.access_links:
            if link.user_id == user_id and not link.disabled:
                return link
        return None

    @staticmethod
    def get_or_create_link(event: Event, user_id: str) -> AccessLink:
        link = LinkAuthService.get_link_for_user(event, user_id)
        if link is None:
            link = AccessLink(
                token=LinkAuthService._generate_token(),
                user_id=user_id,
                created_at=datetime.now().isoformat(),
                disabled=False
            )
            event.access_links.append(link)
            LinkAuthService._persist_event(event)
        return link

    @staticmethod
    def refresh_link(event: Event, user_id: str) -> AccessLink:
        """
        Deaktiviert vorhandene Links und erstellt einen neuen
        """
        for link in event.access_links:
            if link.user_id == user_id:
                link.disabled = True

        new_link = AccessLink(
            token=LinkAuthService._generate_token(),
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            disabled=False
        )
        event.access_links.append(new_link)
        LinkAuthService._persist_event(event)
        return new_link

    @staticmethod
    def disable_link(event: Event, user_id: str):
        changed = False
        for link in event.access_links:
            if link.user_id == user_id and not link.disabled:
                link.disabled = True
                changed = True
        if changed:
            LinkAuthService._persist_event(event)

    @staticmethod
    def resolve_token(token: str) -> Optional[Tuple[Event, AccessLink]]:
        """
        Findet Event + Link zu einem Token
        """
        events = DataManager.load_events()
        for event in events.values():
            for link in event.access_links:
                if not link.disabled and link.token == token:
                    return event, link
        return None

    @staticmethod
    def _persist_event(event: Event):
        try:
            DataManager.update_event(event)
        except AttributeError:
            events = DataManager.load_events()
            events[event.id] = event
            DataManager.save_events(events)
