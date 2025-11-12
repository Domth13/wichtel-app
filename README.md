# Wichtel-App

Streamlit-Anwendung fuer geheimes Weihnachtswichteln mit Magic-Link-Zugriff fuer Teilnehmer.

## Highlights

- Magic-Link Login: Eingeladene Nutzer brauchen nur ihren persoenlichen Link.
- Admin-Dashboard: Events erstellen, starten, loeschen und Links kopieren.
- Automatische Mails: Optionaler Gmail-Versand verschickt die individuellen Links.
- Flexible Speicherung: JSON-Dateien oder MongoDB (per Konfiguration).
- Festliches UI mit Reveal-Animation.

## Installation

1. `pip install -r requirements.txt`
2. `.env.example` in `.env` kopieren und Werte setzen (APP_URL, Gmail-Zugang, MongoDB).
3. (Optional fr Streamlit Cloud) `secrets.example.toml` nach `.streamlit/secrets.toml` kopieren und Werte eintragen.
4. `streamlit run app.py`

## Verwendung

### Admin-Login

- In der App auf **Admin-Login oeffnen** klicken.
- Standardzugang: `anna@test.de` / `temp123` (Passwort nach dem ersten Login aendern).
- Alle anderen Nutzer arbeiten ausschliesslich mit Links.

### Events und Einladungen

1. Als Admin ein Event anlegen und Teilnehmer auswaehlen.
2. Die App erzeugt automatisch einen Token pro Teilnehmer.
3. Im Event-Detail unter **Einladungslinks verwalten** lassen sich alle URLs kopieren oder erneuern.
4. Bei aktivem Mail-Versand enthalten Einladungs- und Startmail automatisch den passenden Link.

### Teilnehmer-Erlebnis

- Der Link sieht aus wie `https://deine-app/-token=...`.
- Vor dem Start sehen Nutzer den Status, nach dem Start koennen sie ihren Wichtel mit einem Klick anzeigen.
- Links bleiben wiederverwendbar, damit Teilnehmer jederzeit nachschauen koennen.

## E-Mail-Versand (optional)

- Nutzt Gmail-App-Passwoerter (siehe `GMAIL_SETUP.md`).
- `APP_URL` muss auf die oeffentliche Streamlit-Adresse zeigen, sonst verweisen die Links ins Leere.
- `SENDER_EMAIL` und `SENDER_PASSWORD` kommen idealerweise aus `.env` oder den Streamlit-Secrets.

## Testdaten

| Rolle  | E-Mail        | Passwort |
|--------|---------------|----------|
| Admin  | anna@test.de  | temp123  |
| Nutzer | max@test.de   | temp123  |
| Nutzer | lisa@test.de  | temp123  |
| Nutzer | tom@test.de   | temp123  |
| Nutzer | sarah@test.de | temp123  |

Nur der Admin benoetigt das Passwort im neuen Flow.

## Projektstruktur

- `app.py`  Einstieg & Routing
- `config.py`  Konstanten
- `models.py`  Datamodelle & Storage
- `link_service.py`  Magic-Link-Service
- `ui_components.py`  Streamlit-Komponenten
- `email_service.py`  Mailversand
- `wichtel_logic.py`  Zuweisungslogik
- `users.json` / `events.json`  Beispieldaten
- `GMAIL_SETUP.md`  Gmail-Anleitung

## Sicherheit

Demoversion fuer private Nutzung. Fuer produktive Einsaetze empfohlen:

- Passwoerter hashen (z. B. bcrypt) und TLS erzwingen.
- Tokens ggf. mit Ablaufdatum/IP-Logging absichern.
- Secrets ausschliesslich per Environment-Variablen verwalten.

Viel Spass beim Wichteln!
