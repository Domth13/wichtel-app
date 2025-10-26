"""
Benutzer-Upload-Skript für die Wichtel-App
Lädt Benutzer aus users_upload.json und speichert sie in der Datenbank
"""
import json
import os
import sys
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Bestimme welche Datenbank verwendet wird
USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() == "true"


def upload_users_from_json(filename: str = "users_upload.json"):
    """
    Lädt Benutzer aus einer JSON-Datei und speichert sie in der Datenbank
    
    Args:
        filename: Pfad zur JSON-Datei mit Benutzerdaten
    """
    # Importiere Models
    from models import User, DataManager
    
    print(f"📂 Lade Benutzer aus '{filename}'...")
    
    # Prüfe ob Datei existiert
    if not os.path.exists(filename):
        print(f"❌ Fehler: Datei '{filename}' nicht gefunden!")
        print(f"\n💡 Erstelle die Datei '{filename}' nach folgendem Format:")
        print("""
{
  "user1": {
    "id": "user1",
    "name": "Anna Schmidt",
    "email": "anna@example.com",
    "password": "temp123",
    "is_admin": true,
    "password_changed": false
  },
  "user2": {
    "id": "user2",
    "name": "Max Müller",
    "email": "max@example.com",
    "password": "temp123",
    "is_admin": false,
    "password_changed": false
  }
}
        """)
        return False
    
    # Lade JSON-Datei
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Fehler beim Parsen der JSON-Datei: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Datei: {e}")
        return False
    
    # Validiere und konvertiere zu User-Objekten
    users = {}
    errors = []
    
    for user_id, user_data in users_data.items():
        try:
            # Prüfe erforderliche Felder
            required_fields = ['id', 'name', 'email', 'password']
            missing_fields = [f for f in required_fields if f not in user_data]
            
            if missing_fields:
                errors.append(f"User '{user_id}': Fehlende Felder: {', '.join(missing_fields)}")
                continue
            
            # Erstelle User-Objekt
            user = User.from_dict(user_data)
            users[user.id] = user
            
        except Exception as e:
            errors.append(f"User '{user_id}': {str(e)}")
    
    # Zeige Fehler
    if errors:
        print(f"\n⚠️ {len(errors)} Fehler beim Validieren:")
        for error in errors:
            print(f"   - {error}")
    
    # Zeige was hochgeladen wird
    if not users:
        print("❌ Keine gültigen Benutzer gefunden!")
        return False
    
    print(f"\n✅ {len(users)} gültige Benutzer gefunden:")
    for user in users.values():
        admin_status = "👑 Admin" if user.is_admin else "👤 User"
        print(f"   - {user.name} ({user.email}) {admin_status}")
    
    # Bestätige Upload
    print(f"\n⚠️  ACHTUNG: Dies überschreibt ALLE bestehenden Benutzer!")
    if USE_MONGODB:
        print(f"   Ziel: MongoDB ({os.getenv('MONGODB_URI', 'localhost')})")
    else:
        print(f"   Ziel: users.json")
    
    response = input("\n❓ Fortfahren? (ja/nein): ").strip().lower()
    
    if response not in ['ja', 'j', 'yes', 'y']:
        print("❌ Abgebrochen.")
        return False
    
    # Speichere in Datenbank
    try:
        DataManager.save_users(users)
        print(f"\n🎉 Erfolgreich! {len(users)} Benutzer hochgeladen.")
        return True
    except Exception as e:
        print(f"\n❌ Fehler beim Speichern: {e}")
        return False


def show_current_users():
    """Zeigt aktuelle Benutzer in der Datenbank"""
    from models import DataManager
    
    print("📊 Aktuelle Benutzer in der Datenbank:")
    
    try:
        users = DataManager.load_users()
        
        if not users:
            print("   (keine Benutzer)")
        else:
            for user in users.values():
                admin_status = "👑 Admin" if user.is_admin else "👤 User"
                pw_status = "✅" if user.password_changed else "🔑 Temp"
                print(f"   - {user.name} ({user.email}) {admin_status} {pw_status}")
        
        print(f"\n   Gesamt: {len(users)} Benutzer")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🎄 Wichtel-App - Benutzer-Upload 🎅")
    print("=" * 60)
    
    if USE_MONGODB:
        print(f"\n📦 Datenbank: MongoDB")
        print(f"   URI: {os.getenv('MONGODB_URI', 'nicht gesetzt')}")
        
        # Teste MongoDB-Verbindung
        try:
            from database import MongoDB
            client = MongoDB.get_client()
            client.admin.command('ping')
            print("   Status: ✅ Verbunden")
        except Exception as e:
            print(f"   Status: ❌ Nicht verbunden ({e})")
            print("\n💡 Stelle sicher, dass MongoDB läuft und die URI korrekt ist.")
            sys.exit(1)
    else:
        print(f"\n📦 Datenbank: JSON-Files")
    
    print()
    print("-" * 60)
    
    # Zeige aktuelle Benutzer
    show_current_users()
    
    print()
    print("-" * 60)
    print()
    
    # Upload durchführen
    filename = input("📂 JSON-Datei (Enter für 'users_upload.json'): ").strip()
    if not filename:
        filename = "users_upload.json"
    
    success = upload_users_from_json(filename)
    
    if success:
        print()
        print("-" * 60)
        print()
        show_current_users()
    
    print()
    print("=" * 60)
    print("Fertig! 🎁")
    print("=" * 60)