"""
Passwort-Hashing ohne zusätzliche Abhängigkeiten.

Format: pbkdf2_sha256$<iterationen>$<salt_b64>$<hash_b64>
Alte Klartext-Passwörter werden beim Login automatisch migriert.
"""
import base64
import hashlib
import hmac
import os
import threading
import time

_attempt_lock = threading.Lock()
_login_attempts = {}


def login_allowed(identity: str, now=None) -> bool:
    """Begrenzt Versuche pro Konto und laufendem App-Prozess."""
    now = time.monotonic() if now is None else now
    identity = (identity or "").strip().casefold()
    with _attempt_lock:
        for key in list(_login_attempts):
            _login_attempts[key] = [t for t in _login_attempts[key] if now - t < 300]
            if not _login_attempts[key]:
                del _login_attempts[key]
        if identity not in _login_attempts and len(_login_attempts) >= 1000:
            return False
        return len(_login_attempts.get(identity, ())) < 5


def record_login_failure(identity: str, now=None):
    now = time.monotonic() if now is None else now
    identity = (identity or "").strip().casefold()
    with _attempt_lock:
        # Begrenzter Speicherbedarf auch bei vielen erfundenen Adressen.
        if identity not in _login_attempts and len(_login_attempts) >= 1000:
            return
        _login_attempts.setdefault(identity, []).append(now)


def clear_login_failures(identity: str):
    with _attempt_lock:
        _login_attempts.pop((identity or "").strip().casefold(), None)

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Erzeugt einen gesalzenen PBKDF2-Hash."""
    password = "" if password is None else str(password)
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    return f"{_ALGORITHM}${_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def is_password_hash(value: str) -> bool:
    return isinstance(value, str) and value.startswith(f"{_ALGORITHM}$")


def verify_password(password: str, stored: str) -> bool:
    """Prüft ein Passwort gegen Hash oder (für Altbestände) Klartext."""
    if not stored:
        return False
    password = "" if password is None else str(password)

    if not is_password_hash(stored):
        # Migration: alte Daten enthalten noch Klartext.
        return hmac.compare_digest(
            password.encode("utf-8"), str(stored).encode("utf-8")
        )

    try:
        _, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        iterations = int(iterations)
        salt = _b64decode(salt_b64)
        expected = _b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
