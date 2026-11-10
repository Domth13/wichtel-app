"""
Setzt das Passwort eines Admin-Kontos zurück.

Beispiele:
    python reset_admin_password.py
    python reset_admin_password.py --email admin@example.com
    python reset_admin_password.py --email admin@example.com --password "NeuesPasswort123!"
"""
import argparse
import secrets
import sys

from dotenv import load_dotenv

from models import DataManager
from security import hash_password, verify_password

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def list_admins():
    users = DataManager.load_users()
    admins = [user for user in users.values() if user.is_admin]
    if not admins:
        print("Keine Admin-Konten gefunden.")
        return
    print("Admin-Konten:")
    for user in sorted(admins, key=lambda item: item.name.lower()):
        status = "Passwort geändert" if user.password_changed else "muss Passwort ändern"
        print(f"  - {user.name} | {user.email} | {status}")


def main():
    parser = argparse.ArgumentParser(description="Admin-Passwort zurücksetzen")
    parser.add_argument("--email", help="E-Mail des Admin-Kontos")
    parser.add_argument(
        "--password",
        help="Neues temporäres Passwort (sonst wird eines erzeugt)",
    )
    args = parser.parse_args()

    load_dotenv()

    if not args.email:
        list_admins()
        return

    user = DataManager.get_user_by_email(args.email)
    if user is None:
        print(f"Kein Benutzer mit E-Mail {args.email} gefunden.")
        raise SystemExit(1)
    if not user.is_admin:
        print(f"{user.email} ist kein Admin-Konto.")
        raise SystemExit(1)

    password = args.password or secrets.token_urlsafe(9)
    if len(password) < 8:
        print("Das Passwort muss mindestens 8 Zeichen haben.")
        raise SystemExit(1)

    user.password = hash_password(password)
    user.password_changed = False
    DataManager.update_user(user)

    if not verify_password(password, user.password):
        print("Fehler: Passwort konnte nicht verifiziert werden.")
        raise SystemExit(1)

    print(f"Passwort für {user.name} ({user.email}) zurückgesetzt.")
    print(f"Temporäres Passwort: {password}")
    print("Beim nächsten Login muss ein neues Passwort gesetzt werden.")


if __name__ == "__main__":
    main()
