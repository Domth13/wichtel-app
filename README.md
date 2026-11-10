# Wichtel-App

Streamlit-App für geheimes Weihnachtswichteln mit **Magic Links** für Teilnehmer und einem Admin-Bereich für die Organisation.

## Was die App kann

- **Teilnehmer**: persönlichen Einladungslink öffnen, Event-Status sehen, Wichtel mit einem Klick anzeigen (und wieder verbergen).
- **Admin**: Events anlegen und bearbeiten, Teilnehmer verwalten, Einladungslinks kopieren/deaktivieren/erneuern, Event starten.
- **Zuweisungen**: zufällig, niemand bekommt sich selbst, jede Person genau einmal.
- **E-Mails**: optional Einladungs- und Startmails über Gmail; sonst Links manuell teilen.
- **Zweisprachig**: Deutsch/Englisch, Umschalter oben rechts.
- **Speicherung**: MongoDB (empfohlen für Cloud) oder JSON-Dateien (lokal).
- **Sicherheit**: Passwörter werden gehasht; vorhandene Klartext-Passwörter werden beim ersten Start automatisch migriert.

## Schnellstart lokal

Unter Windows in PowerShell einmalig die Projektumgebung einrichten:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env  # nur wenn noch keine .env vorhanden ist
```

Danach die App immer mit dem Python aus dieser Umgebung starten:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Alternativ startet `start-windows.bat` die bereits eingerichtete Umgebung.
Ein bloßes `streamlit run app.py` kann eine ältere globale Installation verwenden.

In Git Bash lautet der Startbefehl:

```bash
./.venv/Scripts/python.exe -m streamlit run app.py
```

Das Aktivieren der Umgebung ist dafür nicht erforderlich. Falls gewünscht, lautet
der Befehl dafür `source .venv/Scripts/activate`. Mit `ls -a` werden auch
Verzeichnisse angezeigt, deren Name mit einem Punkt beginnt, etwa `.venv`.

Ohne weitere Konfiguration werden `users.json` und `events.json` im Projektordner verwendet. Diese Dateien sind nicht für Streamlit Community Cloud geeignet (siehe unten).

### Lokal mit MongoDB

Wenn lokal eine MongoDB läuft, reicht eine `.env` im Projektordner:

```toml
APP_URL = "http://localhost:8501"
USE_MONGODB = "true"
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "wichtel_app"
```

Die `.env` ist gitignored. Ein vorhandener Admin in `wichtel_app` wird erkannt; `ADMIN_*` wird nur bei leerer Datenbank benötigt.

## Streamlit Community Cloud + MongoDB

Community Cloud setzt das Dateisystem bei jedem Reboot/Redeploy zurück. JSON-Dateien sind dort **nicht dauerhaft**. Deshalb MongoDB Atlas (kostenloses M0 reicht) verwenden:

1. MongoDB-URI besorgen.
2. In Streamlit Cloud unter **Settings → Secrets** eintragen:

```toml
APP_URL = "https://deine-wichtel-app.streamlit.app"
USE_MONGODB = "true"
MONGODB_URI = "mongodb+srv://user:pass@cluster.mongodb.net/"
DATABASE_NAME = "wichtel_app"

ADMIN_EMAIL = "admin@example.com"
ADMIN_NAME = "Admin"
ADMIN_PASSWORD = "ein-langes-passwort"

# Optional
SENDER_EMAIL = "deine.email@gmail.com"
SENDER_PASSWORD = "dein_app_passwort"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
```

3. `APP_URL` muss die öffentliche App-Adresse sein, sonst zeigen Einladungslinks ins Leere.

### Erster Admin

Wenn noch kein Admin in der Datenbank existiert, legt die App beim Start automatisch einen Admin aus `ADMIN_EMAIL`, `ADMIN_NAME` und `ADMIN_PASSWORD` an. Beim ersten Login muss das Passwort geändert werden. Sobald ein Admin existiert, werden diese Werte nicht mehr überschrieben.

Existiert kein Admin und sind die Variablen nicht gesetzt, zeigt die Startseite einen Hinweis. Lokal bestehende JSON-Daten lassen sich mit `python database.py --migrate` nach MongoDB übernehmen.

### Schläft die Datenbank?

Bei einer schlafenden/ kurzfristig nicht erreichbaren MongoDB zeigt die App eine freundliche Meldung mit **„Erneut verbinden“** statt eines Stacktraces. Einfach antippen, sobald die DB wieder läuft.

## Admin-Workflow

1. Als Admin anmelden (Startseite → **Admin-Bereich**).
2. Unter **Teilnehmer verwalten** Personen mit Name und E-Mail anlegen (bei Bedarf auch per `upload_users.py` lokal importieren – Achtung: das ersetzt die komplette Benutzerliste).
3. **Neues Event erstellen**: Titel, Datum, Ort, Geschenkwert, Hinweis; Teilnehmer auswählen.
4. Optional **Einladungen per E-Mail senden** oder unter **Einladungslinks anzeigen** kopieren/als CSV herunterladen.
5. Event starten (mit Bestätigung). Die Zuweisungen werden gespeichert; danach sind keine Änderungen mehr möglich.
6. Fortschritt „x von y haben ihren Wichtel angesehen“ im Event sehen.

### Admin-Passwort vergessen

```bash
python reset_admin_password.py
python reset_admin_password.py --email admin@example.com --password "TemporaeresPasswort123!"
```

Das Skript setzt ein neues temporäres Passwort und erzwingt beim nächsten Login die Änderung. Ohne `--password` wird eines generiert und angezeigt.

## Teilnehmer-Workflow

1. Link aus der E-Mail öffnen: `https://deine-app.streamlit.app/?token=...`.
2. Vor dem Start: Warte-Karte mit Datum, Ort, Geschenkwert und den nächsten Schritten.
3. Nach dem Start: **Meinen Wichtel anzeigen**; die Karte kann wieder verborgen werden.
4. Der Link bleibt gültig und kann erneut geöffnet werden. Wird er im Admin-Bereich erneuert/deaktiviert, verlieren laufende Sitzungen den Zugriff.

## E-Mail-Versand (optional)

- Gmail benötigt ein **App-Passwort** (2-Faktor-Authentifizierung).
- Ohne konfigurierte SMTP-Daten werden keine Mails versendet; die App zeigt das an und die Links können manuell geteilt werden.
- Der Versand läuft mit Timeout und einer SMTP-Verbindung für alle Empfänger. Fehlgeschlagene Adressen werden angezeigt.

## Lokale Daten und Backup

Die Admin-Anmeldung gilt für die aktuelle Streamlit-Sitzung. Ein vollständiges
Neuladen oder eine neue Browser-Sitzung kann eine erneute Anmeldung erfordern;
die URL der Event-Ansicht ist kein Anmeldetoken. Die Begrenzung fehlgeschlagener
Anmeldungen gilt pro Konto im laufenden App-Prozess und wird bei einem Neustart
zurückgesetzt. Sie ersetzt keinen sitzungsübergreifenden Anmeldedienst.

- JSON-Dateien: `users.json`, `events.json` (beide gitignored).
- Schreibvorgänge sind atomar; bei parallelen Aktionen wird ein Lock verwendet.
- Für ein Backup einfach beide Dateien kopieren; die Einladungslinks lassen sich zusätzlich als CSV exportieren.
- MongoDB-Daten liegen in der konfigurierten Collection `users` / `events`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Projektstruktur

| Datei | Zweck |
|---|---|
| `app.py` | Einstieg, Routing, Session, Fehlerseiten |
| `ui_components.py` | Streamlit-UI, Theme, Event-/Link-Ansichten |
| `models.py` | Datenmodelle, JSON-Speicher, Cache |
| `database.py` | MongoDB-Speicher |
| `security.py` | Passwort-Hashing |
| `link_service.py` | Magic Links |
| `wichtel_logic.py` | Zuweisungslogik |
| `email_service.py` | E-Mail-Templates und Versand |
| `bootstrap.py` | Erster Admin aus Secrets |
| `language.py` | DE/EN-Übersetzungen |
| `flash.py` | Meldungen über `st.rerun()` hinweg |
| `storage_cache.py` | Kurzer Cache für DB-Lesezugriffe |
| `upload_users.py` | Lokaler Massenimport von Benutzern |
| `reset_admin_password.py` | Admin-Passwort per CLI zurücksetzen |
| `.streamlit/config.toml` | Theme und ausgeblendete Entwickler-Toolbar |

## Bekannte Grenzen

- Kein Passwort-Reset per E-Mail. Admins können ihr Passwort im Tab **Konto** ändern oder per `reset_admin_password.py` zurücksetzen.
- Ein Event kann nach dem Start nicht mehr bearbeitet werden.
- Magic Links sind Inhaber-Tokens: Wer den Link hat, sieht die Zuweisung. Links daher nur direkt an die Person weitergeben.
