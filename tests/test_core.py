"""
Kleine Tests für die Kernlogik (ohne Streamlit-Runtime).

Ausführen:
    python -m unittest discover -s tests -v
"""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("USE_MONGODB", "false")

import models
from language import TRANSLATIONS
from link_service import build_invite_url
from email_service import create_event_created_email, create_event_started_email
from security import hash_password, is_password_hash, verify_password
from security import clear_login_failures, login_allowed, record_login_failure
from models import Assignment, DataManager, Event, JSONDataManager
from wichtel_logic import WichtelLogic


class AssignmentTests(unittest.TestCase):
    def _event(self, n):
        ids = [f"p{i}" for i in range(n)]
        return Event(
            id="e1",
            title="Test",
            created_by=ids[0] if ids else "x",
            created_at="2025-01-01T00:00:00",
            participant_ids=ids,
            assignments=[],
        )

    def test_derangement_and_bijection(self):
        with patch.object(DataManager, "update_event_fields", lambda event, fields: None):
            for n in range(2, 25):
                for _ in range(100):
                    event = self._event(n)
                    WichtelLogic.assign_wichtel_random(event)
                    receivers = [item.receiver_id for item in event.assignments]
                    self.assertEqual(sorted(receivers), sorted(event.participant_ids))
                    for item in event.assignments:
                        self.assertNotEqual(item.giver_id, item.receiver_id)

    def test_single_participant_rejected(self):
        with patch.object(DataManager, "update_event_fields", lambda event, fields: None):
            with self.assertRaises(ValueError):
                WichtelLogic.assign_wichtel_random(self._event(1))

    def test_duplicate_participants_rejected(self):
        event = self._event(3)
        event.participant_ids = ["a", "a", "b"]
        with patch.object(DataManager, "update_event_fields", lambda event, fields: None):
            with self.assertRaises(ValueError):
                WichtelLogic.assign_wichtel_random(event)


class SecurityTests(unittest.TestCase):
    def test_login_limit_is_shared_and_expires(self):
        identity = "test-login-limit@example.invalid"
        clear_login_failures(identity)
        try:
            for i in range(5):
                record_login_failure(identity, now=1000 + i)
            self.assertFalse(login_allowed(identity.upper(), now=1005))
            self.assertTrue(login_allowed(identity, now=1305))
        finally:
            clear_login_failures(identity)

    def test_hash_and_verify(self):
        stored = hash_password("geheim123")
        self.assertTrue(is_password_hash(stored))
        self.assertTrue(verify_password("geheim123", stored))
        self.assertFalse(verify_password("falsch", stored))

    def test_legacy_plaintext(self):
        self.assertTrue(verify_password("temp123", "temp123"))
        self.assertFalse(verify_password("falsch", "temp123"))

    def test_empty(self):
        self.assertFalse(verify_password("", ""))
        self.assertFalse(verify_password("x", ""))


class TranslationTests(unittest.TestCase):
    def test_key_parity(self):
        self.assertEqual(set(TRANSLATIONS["de"]), set(TRANSLATIONS["en"]))

    def test_placeholders_match(self):
        import re

        pattern = re.compile(r"\{([a-zA-Z0-9_]+)\}")
        for key, de_text in TRANSLATIONS["de"].items():
            en_text = TRANSLATIONS["en"][key]
            self.assertEqual(set(pattern.findall(de_text)), set(pattern.findall(en_text)), key)


class LinkTests(unittest.TestCase):
    def test_build_url(self):
        self.assertEqual(
            build_invite_url("abc", "https://example.com"),
            "https://example.com?token=abc",
        )
        self.assertEqual(
            build_invite_url("abc", "https://example.com/?x=1"),
            "https://example.com/?x=1&token=abc",
        )

    def test_email_templates_escape_user_input_and_keep_link(self):
        from html.parser import HTMLParser

        class LinkReader(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []

            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    self.links.append(dict(attrs).get("href"))

        url = "https://example.com/?token=abc&lang=en"
        for render in (create_event_created_email, create_event_started_email):
            for lang in ("de", "en"):
                with self.subTest(render=render.__name__, lang=lang):
                    message = render('<Familie & "Freunde">', url, lang)
                    self.assertIn('&lt;Familie &amp; &quot;Freunde&quot;&gt;', message)
                    self.assertNotIn('<Familie', message)
                    self.assertIn(f'<html lang="{lang}">', message)
                    parser = LinkReader()
                    parser.feed(message)
                    self.assertEqual(parser.links, [url])


class ModelTests(unittest.TestCase):
    def test_event_defaults_for_old_docs(self):
        event = Event.from_dict(
            {
                "id": "e1",
                "title": "Alt",
                "created_by": "u1",
                "created_at": "2025-01-01T00:00:00",
                "participant_ids": ["u1", "u2"],
                "assignments": [],
            }
        )
        self.assertFalse(event.is_started)
        self.assertEqual(event.event_date, "")
        self.assertEqual(event.location, "")
        self.assertEqual(event.description, "")

    def test_json_roundtrip_and_reveal(self):
        users_file = os.path.abspath("users.test.json")
        events_file = os.path.abspath("events.test.json")
        for path in (users_file, events_file):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
        try:
            with patch.object(models, "USERS_FILE", users_file), patch.object(
                models, "EVENTS_FILE", events_file
            ):
                from storage_cache import clear

                clear()
                admin = JSONDataManager.create_user(
                    "Admin", "admin@example.com", "passwort123", is_admin=True
                )
                participant = JSONDataManager.create_user(
                    "Max", "max@example.com", "passwort123"
                )
                event = JSONDataManager.create_event(
                    "Wichteln",
                    admin.id,
                    [admin.id, participant.id],
                    "15 EUR",
                    event_date="24.12.",
                    location="Zuhause",
                    description="Mit Essen",
                )
                event.assignments = [
                    Assignment(admin.id, participant.id),
                    Assignment(participant.id, admin.id),
                ]
                JSONDataManager.update_event(event)
                JSONDataManager.mark_revealed(event.id, admin.id)

                # Ein älterer Stand darf die inzwischen erfolgte Offenlegung
                # beim Speichern eines anderen Feldes nicht zurücksetzen.
                event.title = "Neuer Titel"
                JSONDataManager.update_event_fields(event, ("title",))

                loaded_users = JSONDataManager.load_users()
                loaded_event = JSONDataManager.load_events()[event.id]
                self.assertEqual(len(loaded_users), 2)
                self.assertEqual(loaded_event.event_date, "24.12.")
                self.assertEqual(loaded_event.title, "Neuer Titel")
                self.assertEqual(loaded_event.location, "Zuhause")
                self.assertEqual(loaded_event.description, "Mit Essen")
                self.assertTrue(
                    next(
                        item.revealed
                        for item in loaded_event.assignments
                        if item.giver_id == admin.id
                    )
                )
        finally:
            for path in (users_file, events_file):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    unittest.main()
