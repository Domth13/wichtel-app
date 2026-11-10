"""
Service für Magic-Link-Authentifizierung der Teilnehmer.
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlencode

from models import AccessLink, DataManager, Event


def build_invite_url(token: str, base_url: Optional[str] = None) -> str:
    """Baut eine URL für Einladungslinks."""
    base = (base_url or os.getenv("APP_URL") or "http://localhost:8501").rstrip("/")
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{urlencode({'token': token})}"


class LinkAuthService:
    """Verwaltet Einladungs-Links pro Event/Teilnehmer."""
    TOKEN_PREFIX = "wtl_"

    @staticmethod
    def _generate_token() -> str:
        return f"{LinkAuthService.TOKEN_PREFIX}{uuid.uuid4().hex}"

    @staticmethod
    def ensure_links_for_event(event: Event) -> Event:
        """Stellt sicher, dass alle Teilnehmer einen aktiven Link haben."""
        changed = False
        # Auch deaktivierte Links zählen: Ein bewusst deaktivierter Link
        # soll nicht bei jedem Rerun automatisch neu entstehen.
        existing_user_ids = {link.user_id for link in event.access_links}

        for participant_id in event.participant_ids:
            if participant_id not in existing_user_ids:
                event.access_links.append(
                    AccessLink(
                        token=LinkAuthService._generate_token(),
                        user_id=participant_id,
                        created_at=datetime.now().isoformat(),
                        disabled=False,
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
                disabled=False,
            )
            event.access_links.append(link)
            LinkAuthService._persist_event(event)
        return link

    @staticmethod
    def refresh_link(event: Event, user_id: str) -> AccessLink:
        """Deaktiviert vorhandene Links und erstellt einen neuen."""
        for link in event.access_links:
            if link.user_id == user_id:
                link.disabled = True

        new_link = AccessLink(
            token=LinkAuthService._generate_token(),
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            disabled=False,
        )
        event.access_links.append(new_link)
        LinkAuthService._persist_event(event)
        return new_link

    @staticmethod
    def disable_link(event: Event, user_id: str) -> bool:
        changed = False
        for link in event.access_links:
            if link.user_id == user_id and not link.disabled:
                link.disabled = True
                changed = True
        if changed:
            LinkAuthService._persist_event(event)
        return changed

    @staticmethod
    def resolve_token(token: str) -> Optional[Tuple[Event, AccessLink]]:
        """Findet Event + Link zu einem Token."""
        if not token:
            return None
        for event in DataManager.load_events().values():
            for link in event.access_links:
                if not link.disabled and link.token == token:
                    return event, link
        return None

    @staticmethod
    def token_is_active(token: str, user_id: str) -> bool:
        resolved = LinkAuthService.resolve_token(token)
        return bool(
            resolved
            and resolved[1].user_id == user_id
            and user_id in resolved[0].participant_ids
        )

    @staticmethod
    def _persist_event(event: Event):
        DataManager.update_event_fields(event, ("access_links",))
