"""
UI-Komponenten für die Wichtel-App.
"""
import csv
import html
import io
from urllib.parse import urlencode

import streamlit as st

from email_service import (
    EmailConfig,
    email_configured,
    send_event_created_emails,
    send_event_started_emails,
)
from flash import set_flash
from language import set_language
from link_service import LinkAuthService, build_invite_url
from models import DataManager, Event, User
from security import clear_login_failures, hash_password, login_allowed, record_login_failure, verify_password
from wichtel_logic import WichtelLogic


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

_THEME_CSS = """
<style>
:root {
    --bg: #F8FBF9;
    --bg-deep: #EEF5F1;
    --surface: #FFFFFF;
    --surface-soft: #F3F8F5;
    --ink: #20332A;
    --muted: #53685C;
    --green: #205D3D;
    --green-dark: #173F2A;
    --green-soft: #E8F4EC;
    --red: #B3261E;
    --red-dark: #8E1B16;
    --red-soft: #FBE9E7;
    --gold: #C99A2E;
    --gold-soft: #FBF1D8;
    --border: #DCE8E0;
    --shadow: 0 10px 30px rgba(35, 73, 49, 0.05);
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Keine Seite darf breiter als der Viewport werden. Das ist keine Ersatz-
   lösung für Layoutfehler: Streamlit-Columns dürfen dennoch innerhalb der
   verfügbaren Breite schrumpfen; nur dekorativer/technischer Überhang wird
   abgeschnitten. */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    max-width: 100%;
    overflow-x: clip;
}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0;
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(178, 38, 30, 0.035), transparent 26rem),
        linear-gradient(180deg, #FEFFFE 0%, var(--bg) 45%, var(--bg-deep) 100%);
    color: var(--ink);
}

.block-container {
    padding-top: 1.1rem;
    padding-bottom: 4rem;
}

header[data-testid="stHeader"] {
    background: transparent;
    /* Der transparente Header liegt sonst unsichtbar über der Topbar und
       blockiert Klicks auf Sprache/Logout. */
    pointer-events: none;
}

header[data-testid="stHeader"] button,
header[data-testid="stHeader"] a {
    pointer-events: auto;
}

/* Ab Streamlit 1.67 liegt die transparente Toolbar außerhalb von stHeader
   und kann sonst die Bedienelemente der App überdecken. */
div[data-testid="stToolbar"] { pointer-events: none; }
div[data-testid="stToolbar"] button,
div[data-testid="stToolbar"] a { pointer-events: auto; }

#MainMenu, footer {
    visibility: hidden;
}

h1 {
    font-family: Georgia, serif;
    color: var(--red);
    letter-spacing: 0.3px;
}

h2, h3, h4 {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--green);
    font-weight: 700;
    letter-spacing: -0.02em;
}

p, label, .stMarkdown, .stCaption {
    color: var(--ink);
}

/* Die Kopfzeile wird direkt als schlankes HTML/CSS gerendert. */

/* Hero */
.hero {
    text-align: center;
    padding: 1.2rem 0 1.6rem;
}

.hero .hero-emoji {
    font-size: 3.4rem;
    line-height: 1;
    margin-bottom: 0.15rem;
}

.hero h1 {
    font-size: clamp(2.7rem, 7vw, 4.2rem);
    margin: 0;
    color: var(--red);
    text-shadow: 0 2px 0 rgba(255, 255, 255, 0.6);
}

.hero p {
    margin: 0.55rem auto 0;
    max-width: 36rem;
    color: var(--muted);
    font-size: 1.05rem;
    line-height: 1.5;
}

/* Headings */
.page-heading {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: clamp(1.9rem, 4vw, 2.6rem);
    font-weight: 700;
    letter-spacing: -0.04em;
    color: var(--green);
    line-height: 1.1;
    margin: 0.2rem 0 0.15rem;
}

.page-subtitle {
    color: var(--muted);
    font-size: 0.98rem;
    margin: 0 0 1.1rem;
}

/* Kleine Header-Struktur ohne zusätzliche Render-Schicht. */
.app-header {
    display: flex;
    align-items: center;
    min-height: 3.15rem;
    padding: 0.1rem 0 0.65rem;
    margin-bottom: 0.65rem;
    border-bottom: 1px solid var(--border);
}
.app-header-avatar {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    color: var(--green);
    background: var(--green-soft);
    font-size: .82rem;
    font-weight: 700;
}
.app-header-brand { color: var(--green); font-size: .92rem; font-weight: 700; }
.app-header-spacer { flex: 1 1 auto; }
.app-header-languages { display: inline-flex; align-items: center; gap: .22rem; }
.app-header-language { display: inline-flex; align-items: center; justify-content: center; width: 2.1rem; height: 2.1rem; border-radius: 5px; color: var(--muted) !important; text-decoration: none !important; font-size: .78rem; font-weight: 700; }
.app-header-language.active { color: var(--green) !important; background: var(--green-soft); }
.app-header-logout { display: inline-flex; align-items: center; justify-content: center; width: 2.2rem; height: 2.2rem; margin-left: .4rem; color: var(--green) !important; text-decoration: none !important; }
.app-header-logout svg { width: 1.25rem; height: 1.25rem; }
.app-header-language:focus-visible, .app-header-logout:focus-visible { outline: 2px solid rgba(31, 93, 58, .55); outline-offset: 2px; }

.section-label {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}

/* Cards */
/* Nur echte border-Container gestalten. Streamlit 1.39 wraps auch den
   gesamten Seiteninhalt in stVerticalBlockBorderWrapper (emotion-cache-0);
   ein globaler Selektor würde daraus eine einzige riesige Karte machen. */
div[data-testid="stVerticalBlockBorderWrapper"]:not([class*="st-emotion-cache-0"]) {
    background: var(--surface);
    border: 1px solid var(--border) !important;
    border-radius: 20px;
    box-shadow: none;
    padding: 1.6rem;
    margin-bottom: 1.25rem;
}

/* Native Streamlit-Karte: Markup und Aktion bleiben im selben Border-Container.
   Die Schaltfläche selbst wird exakt über dessen komplette Fläche gedehnt. */
.event-open-marker { display: none; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) { position: relative; min-height: 10.5rem; }
/* Streamlit 1.39 adds element wrappers around buttons. They must not become
   the containing block for the full-card button. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) div:has(> div[data-testid="stButton"]) { position: static !important; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) div[data-testid="stButton"] { position: absolute !important; inset: 0; z-index: 2; width: 100% !important; height: 100% !important; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) div[data-testid="stButton"] button { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker):has(button:focus-visible) { outline: 3px solid var(--green); outline-offset: 2px; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) .event-card-status { position: absolute; top: 1.45rem; right: 1.45rem; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) .event-card-arrow { position: absolute; top: 50%; right: 1.45rem; transform: translateY(-50%); color: var(--green); font-size: 2rem; font-weight: 400; line-height: 1; pointer-events: none; }
.event-card-section { margin-bottom: .5rem; color: var(--muted); font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.event-card-title { margin-bottom: .8rem; padding-right: 6.5rem; overflow-wrap: anywhere; font-size: 1.35rem; font-weight: 700; line-height: 1.2; }
.event-card-status { padding: .3rem .7rem; color: var(--green); background: var(--green-soft); border: 1px solid #bfdcc8; border-radius: 999px; font-size: .74rem; font-weight: 700; }
/* Streamlit 1.67 exposes keyed containers as stable CSS classes. */
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] {
    position: relative; background: var(--surface);
    border: 1px solid var(--border) !important; border-radius: 20px;
    padding: 1.6rem; min-height: 10.5rem;
}
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] > div[class*="st-key-open_"] {
    position: static !important; height: 0 !important; min-height: 0 !important;
}
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] div[data-testid="stButton"] { position: static !important; }
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] div[data-testid="stButton"] button {
    position: absolute !important; inset: 0; width: 100% !important;
    height: 100% !important; opacity: 0; cursor: pointer; z-index: 2;
}
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"]:has(button:focus-visible) { outline: 3px solid var(--green); outline-offset: 2px; }
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] .event-card-status { position: absolute; top: 1.45rem; right: 1.45rem; }
div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] .event-card-arrow { position: absolute; top: 50%; right: 1.45rem; transform: translateY(-50%); color: var(--green); font-size: 2rem; line-height: 1; pointer-events: none; }
.card-actions-gap {
    height: 0.7rem;
}

.event-progress {
    height: 6px;
    background: var(--green-soft);
    border-radius: 999px;
    overflow: hidden;
    margin: 0.65rem 0 0.25rem;
}

.event-progress-bar {
    height: 100%;
    background-color: #1F5D3A !important;
    border-radius: 999px;
}

.event-progress-label {
    color: var(--muted);
    font-size: 0.73rem;
}

div[data-testid="stProgress"] div[role="progressbar"] > div > div > div {
    background-color: #1F5D3A !important;
}

div[data-testid="stTabs"] {
    margin-top: 0.35rem;
}

/* Detail rows in the right sidebar */
.detail-row {
    display: flex;
    align-items: flex-start;
    gap: 0.55rem;
    padding: 0.4rem 0;
}

.detail-row .detail-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.7rem;
    height: 1.7rem;
    border-radius: 8px;
    background: var(--surface-soft);
    border: 1px solid var(--border);
    font-size: 0.8rem;
    flex: 0 0 auto;
}

.detail-row .detail-meta {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
    min-width: 0;
}

.detail-row small {
    color: var(--muted);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.detail-row strong {
    color: var(--ink);
    font-size: 0.88rem;
    font-weight: 600;
    overflow-wrap: anywhere;
}

/* Vertical steps for landing page */
.side-steps {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}
.landing-layout { display: grid; grid-template-columns: 1.25fr 1fr; gap: 2rem; align-items: center; }
@media (max-width: 700px) { .landing-layout { grid-template-columns: 1fr; gap: 1.25rem; } }

.side-step {
    display: flex;
    gap: 0.7rem;
    align-items: flex-start;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.75rem 0.85rem;
}

.side-step .step-num {
    flex: 0 0 auto;
}

.side-step strong {
    display: block;
    color: var(--ink);
    font-size: 0.9rem;
    line-height: 1.3;
}

.event-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--ink);
    line-height: 1.2;
    margin-bottom: 0.45rem;
}

.event-hero-title {
    font-size: clamp(1.7rem, 4vw, 2.35rem);
    font-weight: 700;
    color: var(--green);
    line-height: 1.1;
    letter-spacing: -0.035em;
    margin-bottom: 0.45rem;
}

.event-description {
    color: var(--muted);
    font-size: 0.95rem;
    line-height: 1.55;
    margin: 0.65rem 0 0.15rem;
}

/* Chips & pills */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.45rem;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.26rem 0.6rem;
    border-radius: 999px;
    background: var(--surface-soft);
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.78rem;
    white-space: nowrap;
}

.pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    white-space: nowrap;
}

.pill-started {
    background: var(--green-soft);
    color: var(--green);
    border: 1px solid #BFDCC8;
}

.pill-waiting {
    background: var(--gold-soft);
    color: #7A5600;
    border: 1px solid #EBD28F;
}

/* Buttons */
.stButton button,
.stDownloadButton button,
.stFormSubmitButton button {
    border-radius: 11px;
    font-weight: 600;
    border: 1px solid var(--border);
    transition: transform 0.14s ease, box-shadow 0.14s ease, background-color 0.14s ease, border-color 0.14s ease;
    box-shadow: none;
}

.stButton button {
    background: var(--surface);
    color: var(--green);
}
/* Die wichtigste Aktion für Teilnehmer ist gut lesbar und leicht zu treffen. */
div[data-testid="stElementContainer"][class*="st-key-reveal_"] button {
    min-height: 3.5rem;
    padding: .8rem 1rem;
}
div[data-testid="stElementContainer"][class*="st-key-reveal_"] button p {
    font-size: 1.125rem;
    line-height: 1.35;
}
.stButton button[kind="tertiary"],
.stButton button[kind="tertiary"]:hover,
div[data-testid="stTooltipIcon"] button[kind="tertiary"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    color: var(--green) !important;
}

/* Buttons mit help=... werden von Streamlit in stTooltipIcon gewrappt;
   die normalen .stButton-Selektoren greifen dort nicht. */
div[data-testid="stTooltipIcon"] button {
    border-radius: 11px;
    font-weight: 600;
}

div[data-testid="stTooltipIcon"] button[kind="secondary"] {
    background: var(--surface);
    color: var(--green);
    border: 1px solid var(--border);
}

div[data-testid="stTooltipIcon"] button[kind="primary"] {
    background: var(--green) !important;
    border-color: var(--green) !important;
    color: #FFFFFF !important;
}

.stButton button[kind="primary"],
.stFormSubmitButton button {
    background: var(--green) !important;
    background-color: var(--green) !important;
    color: #FFFFFF !important;
    border-color: var(--green) !important;
}

.stButton button[kind="primary"] *,
.stFormSubmitButton button * {
    background: transparent;
    color: #FFFFFF !important;
}

.stDownloadButton button {
    background: var(--surface);
    color: var(--green);
}

.stDownloadButton button:hover {
    background: var(--surface);
    color: var(--green);
    border-color: var(--border);
}

/* Kein Hover-Farbwechsel: auf Touch-Geräten irrelevant und bei breiten
   Buttons wirkt ein reiner Text-Hintergrund unruhig. */
.stButton button:hover {
    background: var(--surface);
    color: var(--green);
    border-color: var(--border);
}

.stButton button[kind="primary"]:hover,
.stFormSubmitButton button:hover {
    background: var(--green) !important;
    color: #FFFFFF !important;
    border-color: var(--green) !important;
}

div[data-testid="stTooltipIcon"] button[kind="secondary"]:hover {
    background: var(--surface);
    color: var(--green);
    border-color: var(--border);
}

div[data-testid="stTooltipIcon"] button[kind="primary"]:hover {
    background: var(--green) !important;
    color: #FFFFFF !important;
    border-color: var(--green) !important;
}

/* Icon-Only-Buttons: Text bleibt für Screenreader im DOM, wird visuell
   aber ausgeblendet. Tooltip liefert die sichtbare Erklärung. */
button:has(span[data-testid="stIconMaterial"]) div[data-testid="stMarkdownContainer"] {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}

.stButton button:has(span[data-testid="stIconMaterial"]),
.stDownloadButton button:has(span[data-testid="stIconMaterial"]) {
    min-width: 2.75rem;
    padding-left: 0.55rem;
    padding-right: 0.55rem;
}

/* Der Marker verankert die Eventkopf-Navigation ohne sichtbaren Leerraum. */
.event-header-marker {
    display: none;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-header-marker) button[kind="secondary"] {
    background: transparent !important; border: 0 !important; box-shadow: none !important;
    color: var(--green) !important; padding: .25rem !important;
}
.topbar-marker { display: none; }
/* Der nicht umbrechende Streamlit-Container scrollt sonst auch vertikal,
   wenn der Absatzabstand der Marke über die Zeile hinausragt. */
div[data-testid="stHorizontalBlock"].st-key-topbar { overflow-y: hidden !important; }
div[data-testid="stHorizontalBlock"].st-key-topbar .stMarkdown p { margin: 0; }
div[data-testid="stVerticalBlock"]:has(> div .topbar-marker) > div[data-testid="stHorizontalBlock"] { align-items: center; gap: .2rem; flex-wrap: nowrap !important; }
div[data-testid="stVerticalBlock"]:has(> div .topbar-marker) > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; }
div[data-testid="stVerticalBlock"]:has(> div .topbar-marker) > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
div[data-testid="stVerticalBlock"]:has(> div .topbar-marker) > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child [data-testid="stMarkdown"] { width: 100% !important; }
div[data-testid="stVerticalBlock"]:has(> div .topbar-marker) > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child [data-testid="stElementContainer"] { width: 100% !important; }
.metrics-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 0 0 1.2rem; }
.metrics-item { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1rem; min-width: 0; }
.metrics-label { color: var(--ink); font-size: .8rem; overflow-wrap: anywhere; }
.metrics-value { color: var(--green); font-size: 2rem; font-weight: 700; line-height: 1.2; margin-top: .35rem; }
.event-title-row { display: flex; align-items: center; justify-content: space-between; gap: .75rem; flex-wrap: wrap; padding-bottom: 1rem; }
.event-title-row .event-hero-title { flex: 1 1 12rem; min-width: 0; margin: 0; overflow-wrap: anywhere; }
.event-title-row .pill { flex: 0 0 auto; }
/* Die Admin-Zeile muss mit mehrzeiligen Titeln wachsen, statt einen eigenen
   Scrollbereich für den horizontalen Streamlit-Container zu erzeugen. */
div[data-testid="stHorizontalBlock"].st-key-event-heading { overflow: visible !important; }

/* Inputs */
div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background: var(--surface-soft) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
}

input, textarea {
    color: var(--ink) !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 600;
    color: var(--muted);
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--green);
}

div[data-baseweb="tab-highlight"] {
    background-color: var(--red);
}

div[data-baseweb="tab-border"] {
    background-color: var(--border);
}

/* Expander */
details[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--surface);
    overflow: hidden;
}

details[data-testid="stExpander"] summary {
    font-weight: 600;
    color: var(--green);
}

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 0.85rem 1rem;
    box-shadow: 0 6px 20px rgba(64, 46, 20, 0.05);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
}

div[data-testid="stMetricValue"] {
    color: var(--green);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-weight: 700;
}

/* Waiting state */
.waiting-card {
    background: linear-gradient(135deg, var(--surface), var(--surface-soft));
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.9rem 1.6rem;
    text-align: center;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.waiting-card .waiting-icon {
    font-size: 3.1rem;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.waiting-card h3 {
    margin: 0 0 0.35rem;
    font-size: 1.5rem;
}

.waiting-card p {
    color: var(--muted);
    margin: 0 auto;
    max-width: 34rem;
    line-height: 1.55;
}

.step-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
}

.step {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.9rem 1rem;
}

.step .step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.55rem;
    height: 1.55rem;
    border-radius: 50%;
    background: var(--red-soft);
    color: var(--red);
    font-weight: 700;
    font-size: 0.78rem;
    margin-bottom: 0.45rem;
}

.step strong {
    display: block;
    color: var(--ink);
    font-size: 0.9rem;
}

/* Reveal */
.wichtel-reveal {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 15% 12%, rgba(255, 255, 255, 0.16), transparent 11rem),
        linear-gradient(135deg, var(--green-dark) 0%, #2A6A45 58%, #3A8357 100%);
    color: #FFFFFF;
    padding: 2.6rem 1.5rem;
    border-radius: 24px;
    text-align: center;
    margin: 1rem 0;
    border: 1px solid rgba(201, 154, 46, 0.65);
    box-shadow: 0 18px 45px rgba(31, 93, 58, 0.25);
    animation: revealAnimation 0.85s cubic-bezier(0.22, 0.9, 0.3, 1.2) both;
}

.wichtel-reveal::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image: radial-gradient(rgba(255, 255, 255, 0.55) 1px, transparent 1px);
    background-size: 26px 26px;
    opacity: 0.12;
    pointer-events: none;
}

.wichtel-reveal .reveal-emoji {
    position: relative;
    font-size: 3rem;
    line-height: 1;
    margin-bottom: 0.35rem;
}

.wichtel-reveal .reveal-label {
    position: relative;
    font-size: 0.85rem;
    opacity: 0.85;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.wichtel-reveal .reveal-name {
    position: relative;
    font-family: Georgia, serif;
    font-size: clamp(2.6rem, 8vw, 4rem);
    font-weight: 700;
    margin: 0.15rem 0 0.5rem;
    color: #F7E6A8;
}

.wichtel-reveal .reveal-gift {
    position: relative;
    display: inline-block;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.22);
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    font-size: 0.9rem;
}

.wichtel-reveal .reveal-hint {
    position: relative;
    margin-top: 0.85rem;
    font-size: 0.82rem;
    opacity: 0.75;
}

@keyframes revealAnimation {
    0%   { opacity: 0; transform: scale(0.82) translateY(26px); }
    60%  { opacity: 1; transform: scale(1.03) translateY(-4px); }
    100% { opacity: 1; transform: scale(1) translateY(0); }
}

/* Landing */
.landing-card {
    background: linear-gradient(135deg, var(--surface), var(--surface-soft));
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.8rem;
    box-shadow: var(--shadow);
    text-align: center;
    margin-bottom: 1rem;
}

.landing-card .landing-icon {
    font-size: 2.5rem;
    line-height: 1;
    margin-bottom: 0.45rem;
}

.landing-card h3 {
    margin: 0 0 0.4rem;
    font-size: 1.4rem;
}

.landing-card p {
    color: var(--muted);
    line-height: 1.6;
    max-width: 38rem;
    margin: 0 auto;
}

/* People */
.person-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--border);
}

.person-row:last-child {
    border-bottom: none;
}

.person-row .person-avatar {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.9rem;
    height: 1.9rem;
    border-radius: 50%;
    background: var(--green-soft);
    color: var(--green);
    font-weight: 700;
    font-size: 0.78rem;
}

.person-row .person-meta {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
    min-width: 0;
}

.person-row strong {
    color: var(--ink);
    font-size: 0.9rem;
}

.person-row small {
    color: var(--muted);
    font-size: 0.78rem;
    overflow-wrap: anywhere;
}

.person-row .person-badge {
    margin-left: auto;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 2.2rem 1rem;
    color: var(--muted);
}

.empty-state .empty-icon {
    font-size: 2.8rem;
    margin-bottom: 0.4rem;
}

.empty-state h3 {
    margin: 0 0 0.3rem;
    color: var(--green);
}

.empty-state p {
    margin: 0 auto;
    max-width: 30rem;
    line-height: 1.55;
}

/* Progress */
.progress-label {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    color: var(--muted);
    font-size: 0.88rem;
    margin-bottom: 0.35rem;
}

/* Soft divider */
.soft-divider {
    height: 1px;
    background: var(--border);
    margin: 1rem 0;
    opacity: 0.8;
}

/* Mobile */
@media (max-width: 700px) {
    .event-title-row .pill { display: none; }
    .block-container {
        padding: 0.75rem 0.9rem 3rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:not([class*="st-emotion-cache-0"]) {
        padding: 1.1rem;
        margin-bottom: 1rem;
    }
    /* Nur echte st.columns stapeln; horizontale Container wie die Kopfzeile
       und der Event-Titel bleiben nebeneinander. */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]) {
        flex-direction: column !important; gap: 1rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: 100% !important; flex: 1 1 auto !important; min-width: 0 !important;
    }

    .metrics-row { gap: .4rem; }
    .metrics-item { padding: .65rem .5rem; border-radius: 12px; }
    .metrics-label { font-size: .65rem; }
    .metrics-value { font-size: 1.45rem; }
    div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] { padding: 1.2rem 1rem; }
    div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] .event-card-status { top: 1.2rem; right: 1rem; }
    div[data-testid="stVerticalBlock"][class*="st-key-event_card_"] .event-card-arrow { right: 1rem; }

    /* Lange Einladungs-URLs bleiben im Codefeld horizontal scrollbar,
       statt die gesamte Dokumentbreite zu vergrößern. */
    div[data-testid="stCode"],
    div[data-testid="stCodeBlock"] {
        max-width: 100%;
        overflow-x: auto;
    }

    .hero {
        padding: 0.7rem 0 1.15rem;
    }
    .hero h1 {
        font-size: 2.7rem;
    }
    .page-heading {
        margin-top: 0.35rem;
    }
    .page-subtitle {
        margin-bottom: 0.9rem;
    }
    .step-grid {
        grid-template-columns: 1fr;
        gap: 0.6rem;
        margin-top: 0.75rem;
    }
    .wichtel-reveal {
        padding: 2rem 1rem;
        margin: 0.75rem 0;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-header-marker) > div > div > div[data-testid="stButton"] {
        position: absolute;
        top: 0.85rem;
        left: 0.85rem;
        z-index: 3;
        width: auto;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-header-marker) > div > div > div[data-testid="stButton"] button {
        min-width: 2rem;
        width: 2rem;
        min-height: 2rem;
        height: 2rem;
        padding: 0;
        background: transparent !important;
        border: 0 !important;
        color: var(--green) !important;
        box-shadow: none !important;
        font-size: 1.35rem;
    }
    .event-hero-title {
        font-size: 1.7rem;
        margin-bottom: 0.35rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) {
        min-height: 11.5rem;
        padding: 1.2rem 1rem;
        border-radius: 18px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) .event-card-status {
        top: 1.2rem;
        right: 1rem;
        padding: .25rem .55rem;
        font-size: .7rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) .event-card-title { font-size: 1.2rem; }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .event-open-marker) .event-card-arrow { right: 1rem; }
    .chip-row {
        gap: 0.3rem;
        margin-top: 0.35rem;
        padding-right: 0;
    }
    .chip {
        padding: 0.22rem 0.48rem;
        font-size: 0.72rem;
    }
    div[data-testid="stTabs"] {
        margin-top: 0.1rem;
    }
    button[data-baseweb="tab"] {
        padding-left: 0.35rem;
        padding-right: 0.35rem;
        font-size: 0.8rem;
    }
    div[data-testid="stMetric"] {
        padding: 0.75rem 0.7rem;
        border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem;
        line-height: 1.2;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.55rem;
    }


}

@media (prefers-reduced-motion: reduce) {
    .wichtel-reveal {
        animation: none;
    }
    .stButton button {
        transition: none;
    }
}

/* Die eigenen HTML-Karten folgen wie Streamlit der Systemeinstellung. */
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #151C18;
        --bg-deep: #101713;
        --surface: #222D26;
        --surface-soft: #2A382F;
        --ink: #EEF3EC;
        --muted: #B6C4B8;
        --green: #9BD7AD;
        --green-dark: #173F2A;
        --green-soft: #294436;
        --red: #F18F86;
        --red-dark: #FFAAA2;
        --red-soft: #50302D;
        --gold: #E9C773;
        --gold-soft: #4B3D24;
        --border: #425347;
        --shadow: 0 10px 30px rgba(0, 0, 0, .2);
    }
    .stApp {
        background: radial-gradient(circle at 8% 0%, rgba(201,154,46,.08), transparent 26rem),
                    linear-gradient(180deg, #1A241D 0%, var(--bg) 42%, var(--bg-deep) 100%);
    }
    .hero h1 { text-shadow: none; }
    div[data-testid="stVerticalBlockBorderWrapper"]:not([class*="st-emotion-cache-0"]),
    div[data-testid="stVerticalBlock"][class*="st-key-event_card_"],
    details[data-testid="stExpander"] { background: var(--surface); }
    .landing-card, .waiting-card { background: linear-gradient(135deg, var(--surface), var(--surface-soft)); }
    .pill-started, .event-card-status { border-color: #537D60; }
    .pill-waiting { color: #F4D999; border-color: #8B7345; }
    .person-row { border-color: var(--border); }
    .event-progress-bar, div[data-testid="stProgress"] div[role="progressbar"] > div > div > div {
        background-color: #9BD7AD !important;
    }
    .stButton button[kind="primary"], .stFormSubmitButton button,
    div[data-testid="stTooltipIcon"] button[kind="primary"] {
        background: #285F40 !important; border-color: #285F40 !important; color: #FFFFFF !important;
    }
}
</style>
"""


def apply_christmas_theme():
    """Injiziert das weihnachtliche Theme."""
    st.html(_THEME_CSS)


# ---------------------------------------------------------------------------
# Sprache / Kopfzeile
# ---------------------------------------------------------------------------

def _query_url(**changes) -> str:
    """Erstellt einen Link, der vorhandene URL-Parameter erhält."""
    params = {key: value for key, value in st.query_params.items() if key not in changes}
    params.update({key: value for key, value in changes.items() if value is not None})
    return "?" + urlencode(params, doseq=True)


def show_topbar(user: User, _):
    """Kopfzeile mit Streamlit-Aktionen, die die Sitzung erhalten."""
    requested_language = st.query_params.get("lang")
    if requested_language in {"de", "en"} and requested_language != st.session_state.get("language"):
        set_language(requested_language)

    is_admin = bool(user and user.is_admin)
    with st.container(horizontal=True, vertical_alignment="center", gap="xxsmall", wrap=False, key="topbar"):
        st.markdown("**🎄 Wichtel**", width="stretch")
        for code in ("de", "en"):
            if st.button(code.upper(), key=f"language_{code}", type="tertiary", disabled=st.session_state.get("language") == code):
                set_language(code)
                st.rerun()
        if is_admin:
            if st.button(_("logout_button"), key="logout", type="tertiary", icon=":material/logout:", help=_("logout_button")):
                language = st.session_state.get("language", "de")
                st.session_state.clear()
                st.session_state.language = language
                _navigate_to(lang=language)


# ---------------------------------------------------------------------------
# Login / Passwort
# ---------------------------------------------------------------------------

def show_login_form(_):
    """Schlanker Login im bereits eindeutig benannten Admin-Bereich."""
    with st.container(border=True):
        with st.form("login_form"):
            email = st.text_input(_("email_label"), placeholder="anna@example.com")
            password = st.text_input(_("password_label"), type="password")
            submit = st.form_submit_button(
                _("login_button"), use_container_width=True, type="primary"
            )

            if not submit:
                return

            if not login_allowed(email):
                st.error(_("too_many_login_attempts"))
                return

            user = DataManager.authenticate(email, password)
            if not user or not user.is_admin:
                record_login_failure(email)
                st.error(_("invalid_credentials"))
                return

            clear_login_failures(email)

            if not user.password_changed:
                st.session_state.temp_user = user
                st.session_state.show_password_change = True
                st.rerun()
                return

            st.session_state.user = user
            # Die Dashboard-Überschrift begrüßt bereits persönlich; keine
            # zweite grüne Erfolgsmitteilung darüber anzeigen.
            st.rerun()


def show_password_change_form(_):
    """Erzwungener Passwortwechsel beim ersten Login."""
    user = st.session_state.get("temp_user")
    if user is None:
        st.session_state.pop("show_password_change", None)
        set_flash("warning", _("invalid_credentials"))
        st.rerun()

    st.markdown('<div class="page-heading">' + _("change_password_header") + "</div>", unsafe_allow_html=True)
    st.caption(_("change_password_info"))

    with st.container(border=True):
        st.write(f"**{_('account')}:** {user.name} ({user.email})")
        with st.form("password_change_form"):
            new_password = st.text_input(_("new_password"), type="password")
            confirm_password = st.text_input(_("confirm_password"), type="password")
            submit = st.form_submit_button(
                _("save_button"), use_container_width=True, type="primary"
            )

            if not submit:
                return

            if not new_password:
                st.error(_("password_empty"))
                return
            if len(new_password) < 8:
                st.error(_("password_too_short"))
                return
            if new_password != confirm_password:
                st.error(_("passwords_not_match"))
                return

            user.password = hash_password(new_password)
            user.password_changed = True
            DataManager.update_user(user)
            st.session_state.user = user
            st.session_state.pop("temp_user", None)
            st.session_state.pop("show_password_change", None)
            set_flash("success", _("password_saved"), balloons=True)
            st.rerun()


def show_account_settings(user: User, _):
    """Passwort des eingeloggten Admins ändern."""
    if not user.is_admin:
        return

    left, right = st.columns([1.35, 1], gap="large")

    with left:
        st.markdown("### " + _("account_settings"))
        st.caption(_("account_settings_hint"))

        with st.container(border=True):
            with st.form("change_own_password"):
                current_password = st.text_input(_("current_password"), type="password")
                new_password = st.text_input(_("new_password"), type="password")
                confirm_password = st.text_input(_("confirm_password"), type="password")
                submit = st.form_submit_button(
                    _("save_button"), type="primary", use_container_width=True
                )

                if submit:
                    if not verify_password(current_password, user.password):
                        st.error(_("password_wrong"))
                    elif len(new_password) < 8:
                        st.error(_("password_too_short"))
                    elif new_password != confirm_password:
                        st.error(_("passwords_not_match"))
                    else:
                        user.password = hash_password(new_password)
                        user.password_changed = True
                        DataManager.update_user(user)
                        set_flash("success", _("password_saved"), balloons=True)
                        st.rerun()

    with right:
        st.markdown("### " + _("security_tips"))
        with st.container(border=True):
            for icon, text in (
                ("🔒", _("security_tip_1")),
                ("🔗", _("security_tip_2")),
                ("🔄", _("security_tip_3")),
            ):
                st.markdown(
                    f'<div class="detail-row"><span class="detail-icon">{icon}</span>'
                    f'<span class="detail-meta"><strong>{html.escape(text)}</strong></span></div>',
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------

def _navigate_to(**params) -> None:
    """Aktualisiert Query-Parameter als leichter Navigationsmechanismus."""
    st.query_params.clear()
    st.query_params.update(params)
    st.rerun()


def _status_pill(started: bool, _) -> str:
    label = _("started") if started else _("waiting")
    css = "pill-started" if started else "pill-waiting"
    return f'<span class="pill {css}">{html.escape(label)}</span>'


def _chip(text: str) -> str:
    return f'<span class="chip">{text}</span>'


def _event_chips(event: Event, _) -> str:
    chips = [_chip(f"👥 {_('participants', count=len(event.participant_ids))}")]
    if event.event_date:
        chips.append(_chip(f"📅 {html.escape(event.event_date)}"))
    if event.location:
        chips.append(_chip(f"📍 {html.escape(event.location)}"))
    if event.gift_value:
        chips.append(_chip(f"🎁 {html.escape(_('gift_value', value=event.gift_value))}"))
    return '<div class="chip-row">' + "".join(chips) + "</div>"


def _page_heading(text: str, subtitle: str = ""):
    st.markdown(
        f'<div class="page-heading">{html.escape(text)}</div>'
        + (f'<div class="page-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Event-Liste / Anlegen / Teilnehmer
# ---------------------------------------------------------------------------

def _event_card_chips(event: Event, _) -> list[str]:
    """Liefert die kompakten Fakten für die eigenständige Eventkarten-Komponente."""
    chips = [f"👥 {_('participants', count=len(event.participant_ids))}"]
    if event.event_date:
        chips.append(f"📅 {event.event_date}")
    if event.location:
        chips.append(f"📍 {event.location}")
    if event.gift_value:
        chips.append(f"🎁 {_('gift_value', value=event.gift_value)}")
    return chips


def show_event_list(user: User, _, events=None):
    """Event-Liste für Admins mit vollständig klickbaren Eventkarten."""
    if events is None:
        events = WichtelLogic.get_user_events(user.id)
    if not events:
        st.markdown(
            f'<div class="empty-state"><div class="empty-icon">🎄</div>'
            f"<h3>{html.escape(_('empty_events_title'))}</h3>"
            f"<p>{html.escape(_('empty_events_text'))}</p></div>",
            unsafe_allow_html=True,
        )
        return

    for event in events:
        # Ein nativer Button deckt die Karte ab und bleibt per Tastatur bedienbar.
        with st.container(border=True, key=f"event_card_{event.id}"):
            st.markdown('<span class="event-open-marker"></span>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="event-card-section">{html.escape(_("section_event"))}</div>'
                f'<div class="event-card-title">{html.escape(event.title)}</div>'
                f'<span class="event-card-status">{html.escape(_("started") if event.is_started else _("waiting"))}</span>'
                f'<div class="chip-row">'
                f"{''.join(f'<span class=\"chip\">{html.escape(chip)}</span>' for chip in _event_card_chips(event, _))}</div>",
                unsafe_allow_html=True,
            )
            if event.is_started and event.assignments:
                done = sum(1 for item in event.assignments if item.revealed)
                total = len(event.assignments)
                percent = int(done / total * 100) if total else 0
                st.markdown(
                    f'<div class="event-progress"><div class="event-progress-bar" style="width:{percent}%"></div></div>'
                    f'<div class="event-progress-label">'
                    f'{html.escape(_("progress_revealed", done=done, total=total))}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('<span class="event-card-arrow" aria-hidden="true">→</span>', unsafe_allow_html=True)
            if st.button(_("open_event"), key=f"open_{event.id}", use_container_width=True):
                st.session_state.current_event = event.id
                st.query_params["event"] = event.id
                st.rerun()


def show_admin_side_panel(events, users, _):
    """Kleine Status-/Tipp-Karten für die rechte Dashboard-Spalte."""
    next_event = None
    if events:
        next_event = next((event for event in events if not event.is_started), events[0])

    with st.container(border=True):
        st.markdown(
            f'<div class="section-label">{html.escape(_("next_step"))}</div>',
            unsafe_allow_html=True,
        )
        if next_event is None:
            icon = "🎄"
            title = _("next_step_empty_title")
            text = _("next_step_empty_text")
        elif not next_event.is_started:
            icon = "✉️"
            title = _("next_step_wait_title")
            text = _("next_step_wait_text")
        else:
            icon = "🎁"
            done = sum(1 for item in next_event.assignments if item.revealed)
            total = len(next_event.assignments)
            title = _("next_step_run_title")
            text = _("next_step_run_text", done=done, total=total)
        st.markdown(
            f'<div class="detail-row"><span class="detail-icon">{icon}</span>'
            f'<span class="detail-meta"><strong>{html.escape(title)}</strong>'
            f'<small style="text-transform:none; letter-spacing:0; font-size:0.8rem; line-height:1.45;">'
            f'{html.escape(text)}</small></span></div>',
            unsafe_allow_html=True,
        )


def show_create_event_form(user: User, _, expanded: bool = False):
    """Formular zum Anlegen eines Events."""
    if not user.is_admin:
        return

    users = DataManager.load_users()
    options = {uid: item.name for uid, item in users.items() if uid != user.id}

    with st.expander(_("create_new_event"), expanded=expanded):
        with st.form("create_event_form"):
            title = st.text_input(_("event_title"), placeholder=_("event_title_placeholder"))

            date_col, location_col = st.columns(2)
            with date_col:
                event_date = st.text_input(
                    _("event_date_label"), placeholder=_("event_date_placeholder")
                )
            with location_col:
                location = st.text_input(
                    _("event_location_label"), placeholder=_("event_location_placeholder")
                )

            gift_value = st.text_input(
                _("gift_value_optional"), placeholder=_("gift_value_placeholder")
            )
            description = st.text_area(
                _("event_description_label"),
                placeholder=_("event_description_placeholder"),
                height=80,
            )

            include_self = st.checkbox(_("include_self"), value=True)
            selected_users = st.multiselect(
                _("select_participants"),
                options=list(options.keys()),
                format_func=lambda uid: options[uid],
                placeholder=_("participants_placeholder"),
            )
            if not options:
                st.caption(_("no_other_participants"))

            submit = st.form_submit_button(
                _("create_event_button"), type="primary", use_container_width=True
            )

            if not submit:
                return

            if not title.strip():
                st.warning(_("title_participants_missing"))
                return

            participant_ids = ([user.id] if include_self else []) + selected_users
            participant_ids = list(dict.fromkeys(participant_ids))
            if len(participant_ids) < 2:
                st.warning(_("min_two_participants"))
                return

            event = DataManager.create_event(
                title,
                user.id,
                participant_ids,
                gift_value,
                event_date=event_date,
                location=location,
                description=description,
            )
            LinkAuthService.ensure_links_for_event(event)
            st.session_state.current_event = event.id
            st.query_params["event"] = event.id
            set_flash("success", _("event_created", title=title), balloons=True)
            st.rerun()


def show_user_management(user: User, _):
    """Teilnehmerverwaltung für Admins."""
    if not user.is_admin:
        return

    users = DataManager.load_users()
    left, right = st.columns([1.6, 1], gap="large")

    with left:
        st.markdown("### " + _("manage_participants"))
        st.caption(_("participants", count=len(users)))

        with st.container(border=True):
            if users:
                for item in sorted(users.values(), key=lambda entry: entry.name.lower()):
                    initial = (item.name or "?").strip()[:1].upper() or "?"
                    badge = (
                        f'<span class="person-badge">{_("admin_badge")}</span>'
                        if item.is_admin
                        else ""
                    )
                    st.markdown(
                        f'<div class="person-row"><span class="person-avatar">{html.escape(initial)}</span>'
                        f'<span class="person-meta"><strong>{html.escape(item.name)}</strong>'
                        f"<small>{html.escape(item.email)}</small></span>{badge}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info(_("no_other_participants"))

    with right:
        st.markdown("### " + _("add_participant"))
        st.caption(_("add_participant_hint"))
        with st.container(border=True):
            with st.form("add_participant_form", clear_on_submit=True):
                name = st.text_input(_("name_label"))
                email = st.text_input(_("email_label"))
                submit = st.form_submit_button(
                    _("add_button"), type="primary", use_container_width=True
                )

                if submit:
                    try:
                        DataManager.create_user(name, email)
                    except ValueError as exc:
                        key = str(exc)
                        message = (
                            _("participant_exists") if key == "email_exists" else _(key)
                        )
                        st.error(message)
                    else:
                        set_flash("success", _("participant_added", name=name.strip()))
                        st.rerun()



# ---------------------------------------------------------------------------
# Event-Ansichten
# ---------------------------------------------------------------------------

def _show_waiting_card(event: Event, _):
    """Wartehinweis ohne erneut alle Fakten aus dem Event-Header zu wiederholen."""
    st.markdown(
        f'<div class="waiting-card"><div class="waiting-icon">🎁</div>'
        f"<h3>{html.escape(_('waiting_title'))}</h3>"
        f"<p>{html.escape(_('event_not_started_help'))}</p></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="step-grid">'
        f'<div class="step"><span class="step-num">1</span><strong>{html.escape(_("step_1"))}</strong></div>'
        f'<div class="step"><span class="step-num">2</span><strong>{html.escape(_("step_2"))}</strong></div>'
        f'<div class="step"><span class="step-num">3</span><strong>{html.escape(_("step_3"))}</strong></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _show_reveal(event: Event, user: User, users, _, assignment):
    visible_key = f"reveal_visible_{event.id}_{user.id}"
    celebrate_key = f"reveal_celebrate_{event.id}_{user.id}"

    if not st.session_state.get(visible_key):
        if st.button(
            _("show_my_wichtel"),
            type="primary",
            use_container_width=True,
            key=f"reveal_{event.id}_{user.id}",
        ):
            if not assignment.revealed:
                WichtelLogic.reveal_assignment(event, user.id)
            st.session_state[visible_key] = True
            st.session_state[celebrate_key] = True
            st.rerun()
        return

    if st.session_state.pop(celebrate_key, False):
        st.balloons()

    receiver = users.get(assignment.receiver_id)
    receiver_name = receiver.name if receiver else _("unknown")
    gift_html = ""
    if event.gift_value:
        gift_html = (
            f'<div class="reveal-gift">'
            f'{html.escape(_("gift_value_display", value=event.gift_value))}</div>'
        )

    st.markdown(
        f"""
        <div class="wichtel-reveal">
            <div class="reveal-emoji">🎁</div>
            <div class="reveal-label">{html.escape(_("you_wichtel_for"))}</div>
            <div class="reveal-name">{html.escape(receiver_name)}</div>
            {gift_html}
            <div class="reveal-hint">{html.escape(_("reveal_hint"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        _("reveal_hide"),
        key=f"hide_{event.id}_{user.id}",
        icon=":material/visibility_off:",
        help=_("reveal_hide"),
    ):
        st.session_state[visible_key] = False
        st.rerun()


def _show_start_section(event: Event, _):
    st.markdown("### " + _("start_assignments"))
    st.caption(_("start_hint"))

    confirm_key = f"confirm_start_{event.id}"
    if st.session_state.get(confirm_key):
        st.warning(_("start_confirm"))
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button(
                _("start_now"),
                type="primary",
                use_container_width=True,
                key=f"start_now_{event.id}",
            ):
                try:
                    WichtelLogic.assign_wichtel_random(event)
                    with st.spinner(_("sending")):
                        result = send_event_started_emails(
                            event, lang=st.session_state.get("language", "de")
                        )
                except ValueError as exc:
                    st.error(_(str(exc)))
                    return

                st.session_state.pop(confirm_key, None)
                total = len(result["sent"]) + len(result["failed"])
                if result.get("skipped"):
                    email_message = _("email_not_configured")
                else:
                    email_message = _(
                        "startmails_result", sent=len(result["sent"]), total=total
                    )
                details = []
                if result["failed"] and not result.get("skipped"):
                    details.append(
                        _("email_failed_for", emails=", ".join(result["failed"]))
                    )
                set_flash(
                    "warning"
                    if result["failed"] and not result.get("skipped")
                    else "success",
                    f"{_('assignments_created')} {email_message}",
                    balloons=True,
                    details=details,
                )
                st.rerun()
        with no_col:
            if st.button(_("cancel"), use_container_width=True, key=f"cancel_start_{event.id}"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
    else:
        if st.button(
            _("start_assignments"),
            type="primary",
            key=f"start_{event.id}",
        ):
            st.session_state[confirm_key] = True
            st.rerun()


def _show_progress(event: Event, _):
    total = len(event.assignments)
    if not total:
        return
    done = sum(1 for item in event.assignments if item.revealed)
    with st.container(border=True):
        st.markdown(
            f'<div class="progress-label"><span>{html.escape(_("progress_revealed", done=done, total=total))}</span>'
            f"<strong>{done}/{total}</strong></div>",
            unsafe_allow_html=True,
        )
        st.progress(done / total)


def _show_send_invites(event: Event, _):
    st.markdown("### " + _("send_invites"))
    if not email_configured():
        st.caption(_("email_not_configured"))
        return

    app_url = EmailConfig.APP_URL or ""
    if not app_url or "localhost" in app_url or "127.0.0.1" in app_url:
        st.warning(_("link_base_warning"))

    if st.button(
        _("send_invites"),
        type="primary",
        key=f"send_invites_{event.id}",
    ):
        with st.spinner(_("sending")):
            result = send_event_created_emails(
                event, lang=st.session_state.get("language", "de")
            )
        total = len(result["sent"]) + len(result["failed"])
        if result.get("skipped"):
            set_flash("warning", _("email_not_configured"))
        else:
            details = []
            if result["failed"]:
                details.append(
                    _("email_failed_for", emails=", ".join(result["failed"]))
                )
            set_flash(
                "warning"
                if result["failed"] and not result.get("skipped")
                else "success",
                _("invites_result", sent=len(result["sent"]), total=total),
                details=details,
            )
        st.rerun()


def _show_invite_links(event: Event, users, _):
    if not st.toggle(_("show_invite_links"), key=f"show_links_{event.id}"):
        return

    app_url = EmailConfig.APP_URL or ""
    if not app_url or "localhost" in app_url or "127.0.0.1" in app_url:
        st.warning(_("link_base_warning"))

    rows = []
    for index, participant_id in enumerate(event.participant_ids):
        participant = users.get(participant_id)
        if not participant:
            continue

        if index:
            st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="person-row"><span class="person-avatar">'
            f'{(participant.name or "?").strip()[:1].upper()}</span>'
            f'<span class="person-meta"><strong>{html.escape(participant.name)}</strong>'
            f"<small>{html.escape(participant.email)}</small></span></div>",
            unsafe_allow_html=True,
        )

        link = LinkAuthService.get_link_for_user(event, participant_id)
        if link is None:
            st.caption(_("no_active_link"))
            if st.button(
                _("create_link"),
                key=f"create_link_{event.id}_{participant_id}",
                icon=":material/add_link:",
                help=_("create_link"),
            ):
                LinkAuthService.get_or_create_link(event, participant_id)
                set_flash("success", _("link_created"))
                st.rerun()
            continue

        invite_url = build_invite_url(link.token, app_url)
        rows.append([participant.name, participant.email, invite_url])
        st.code(invite_url, language=None)

        refresh_confirm = f"confirm_refresh_{event.id}_{participant_id}"
        disable_confirm = f"confirm_disable_{event.id}_{participant_id}"
        button_cols = st.columns([1, 1, 3])
        with button_cols[0]:
            if st.button(
                _("refresh_link", name=participant.name),
                key=f"refresh_{event.id}_{participant_id}",
                icon=":material/refresh:",
                help=_("refresh_link", name=participant.name),
            ):
                st.session_state[refresh_confirm] = True
                st.rerun()
        with button_cols[1]:
            if st.button(
                _("disable_link"),
                key=f"disable_{event.id}_{participant_id}",
                icon=":material/link_off:",
                help=_("disable_link"),
            ):
                st.session_state[disable_confirm] = True
                st.rerun()

        if st.session_state.get(refresh_confirm):
            st.warning(_("confirm_refresh_link", name=participant.name))
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button(
                    _("yes"),
                    key=f"yes_refresh_{event.id}_{participant_id}",
                    use_container_width=True,
                ):
                    LinkAuthService.refresh_link(event, participant_id)
                    st.session_state.pop(refresh_confirm, None)
                    set_flash("success", _("link_refreshed"))
                    st.rerun()
            with no_col:
                if st.button(
                    _("no"),
                    key=f"no_refresh_{event.id}_{participant_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(refresh_confirm, None)
                    st.rerun()

        if st.session_state.get(disable_confirm):
            st.warning(_("confirm_disable_link", name=participant.name))
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button(
                    _("yes"),
                    key=f"yes_disable_{event.id}_{participant_id}",
                    use_container_width=True,
                ):
                    LinkAuthService.disable_link(event, participant_id)
                    st.session_state.pop(disable_confirm, None)
                    set_flash("success", _("link_disabled", name=participant.name))
                    st.rerun()
            with no_col:
                if st.button(
                    _("no"),
                    key=f"no_disable_{event.id}_{participant_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(disable_confirm, None)
                    st.rerun()

    if rows:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([_("csv_name"), _("csv_email"), _("csv_link")])
        writer.writerows(rows)
        st.download_button(
            _("download_links_csv"),
            data=buffer.getvalue().encode("utf-8"),
            file_name=f"wichtel-links-{event.id}.csv",
            mime="text/csv",
            key=f"csv_{event.id}",
            icon=":material/download:",
            help=_("download_links_csv"),
        )


def _show_edit_event(event: Event, user: User, users, _):
    st.markdown("### " + _("edit_event"))
    if event.is_started:
        st.info(_("event_locked"))
        return

    options = {uid: item.name for uid, item in users.items() if uid != user.id}
    current_selection = [
        pid for pid in event.participant_ids if pid != user.id and pid in options
    ]

    with st.container(border=True):
        with st.form(f"edit_event_form_{event.id}"):
            title = st.text_input(_("event_title"), value=event.title)
            date_col, location_col = st.columns(2)
            with date_col:
                event_date = st.text_input(
                    _("event_date_label"),
                    value=event.event_date,
                    placeholder=_("event_date_placeholder"),
                )
            with location_col:
                location = st.text_input(
                    _("event_location_label"),
                    value=event.location,
                    placeholder=_("event_location_placeholder"),
                )
            gift_value = st.text_input(
                _("gift_value_optional"),
                value=event.gift_value,
                placeholder=_("gift_value_placeholder"),
            )
            description = st.text_area(
                _("event_description_label"),
                value=event.description,
                placeholder=_("event_description_placeholder"),
                height=80,
            )
            include_self = st.checkbox(
                _("include_self"), value=user.id in event.participant_ids
            )
            selected = st.multiselect(
                _("select_participants"),
                options=list(options.keys()),
                default=current_selection,
                format_func=lambda uid: options[uid],
                placeholder=_("participants_placeholder"),
            )
            submit = st.form_submit_button(
                _("save_changes"), type="primary", use_container_width=True
            )

            if not submit:
                return

            if not title.strip():
                st.warning(_("title_participants_missing"))
                return

            new_ids = ([user.id] if include_self else []) + selected
            new_ids = list(dict.fromkeys(new_ids))
            if len(new_ids) < 2:
                st.warning(_("min_two_participants"))
                return

            old_ids = set(event.participant_ids)
            removed = old_ids - set(new_ids)
            added = set(new_ids) - old_ids
            event.title = title.strip()
            event.event_date = event_date.strip()
            event.location = location.strip()
            event.gift_value = gift_value.strip()
            event.description = description.strip()
            event.participant_ids = new_ids

            DataManager.update_event_fields(
                event, ("title", "event_date", "location", "gift_value", "description", "participant_ids")
            )
            for participant_id in added:
                LinkAuthService.get_or_create_link(event, participant_id)
            LinkAuthService.ensure_links_for_event(event)
            for participant_id in removed:
                LinkAuthService.disable_link(event, participant_id)

            set_flash("success", _("event_updated", title=event.title))
            st.rerun()


def _show_delete_event(event: Event, _):
    st.markdown("### " + _("delete_button"))
    st.caption(
        _("delete_started_hint") if event.is_started else _("confirm_delete_event", title=event.title)
    )

    confirm_key = f"delete_event_confirm_{event.id}"
    if st.session_state.get(confirm_key):
        st.warning(_("confirm_delete_event", title=event.title))
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button(
                _("yes_delete"),
                key=f"delete_yes_{event.id}",
                use_container_width=True,
            ):
                DataManager.delete_event(event.id)
                st.session_state.current_event = None
                if "event" in st.query_params:
                    del st.query_params["event"]
                st.session_state.pop(confirm_key, None)
                set_flash("success", _("event_deleted"))
                st.rerun()
        with no_col:
            if st.button(
                _("cancel"),
                key=f"delete_no_{event.id}",
                use_container_width=True,
            ):
                st.session_state.pop(confirm_key, None)
                st.rerun()
    else:
        if st.button(
            _("delete_button"),
            key=f"delete_event_{event.id}",
            icon=":material/delete:",
            help=_("delete_button"),
        ):
            st.session_state[confirm_key] = True
            st.rerun()


def _show_details_card(event: Event, users, _, admin_view: bool, wide: bool = False):
    details = []
    if event.event_date:
        details.append(("📅", _("detail_date"), event.event_date))
    if event.location:
        details.append(("📍", _("detail_location"), event.location))
    if event.gift_value:
        details.append(("🎁", _("detail_gift"), event.gift_value))
    creator = users.get(event.created_by)
    details.append(
        ("👤", _("detail_created_by"), creator.name if creator else _("unknown"))
    )
    details_html = "".join(
        f'<div class="detail-row"><span class="detail-icon">{icon}</span>'
        f'<span class="detail-meta"><small>{html.escape(label)}</small>'
        f"<strong>{html.escape(value)}</strong></span></div>"
        for icon, label, value in details
    )

    revealed = {item.giver_id: item.revealed for item in event.assignments}
    participants_html = ""
    for participant_id in event.participant_ids:
        participant = users.get(participant_id)
        if not participant:
            continue
        initial = (participant.name or "?").strip()[:1].upper() or "?"
        suffix = ""
        if admin_view and event.is_started and revealed.get(participant_id):
            suffix = ' <span class="pill pill-started" style="font-size:0.65rem;padding:0.15rem 0.45rem;">✓</span>'
        participants_html += (
            f'<div class="person-row"><span class="person-avatar">{html.escape(initial)}</span>'
            f'<span class="person-meta"><strong>{html.escape(participant.name)}</strong></span>'
            f"{suffix}</div>"
        )

    with st.container(border=True):
        if wide:
            left_col, right_col = st.columns(2, gap="large")
            with left_col:
                st.markdown(
                    f'<div class="section-label">{html.escape(_("event_details"))}</div>{details_html}',
                    unsafe_allow_html=True,
                )
            with right_col:
                st.markdown(
                    f'<div class="section-label">{html.escape(_("all_participants"))}</div>{participants_html}',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div class="section-label">{html.escape(_("event_details"))}</div>{details_html}'
                f'<div class="soft-divider"></div>'
                f'<div class="section-label">{html.escape(_("all_participants"))}</div>{participants_html}',
                unsafe_allow_html=True,
            )


def _show_pending_participants(event: Event, users, _):
    revealed = {item.giver_id: item.revealed for item in event.assignments}
    pending = [
        participant_id
        for participant_id in event.participant_ids
        if not revealed.get(participant_id)
    ]

    with st.container(border=True):
        st.markdown(
            f'<div class="section-label">{html.escape(_("pending_title"))}</div>',
            unsafe_allow_html=True,
        )
        if not pending:
            st.markdown(
                f'<div class="detail-row"><span class="detail-icon">✓</span>'
                f'<span class="detail-meta"><strong>{html.escape(_("all_seen"))}</strong></span></div>',
                unsafe_allow_html=True,
            )
            return

        pending_columns = st.columns(2)
        for index, participant_id in enumerate(pending):
            participant = users.get(participant_id)
            if not participant:
                continue
            initial = (participant.name or "?").strip()[:1].upper() or "?"
            with pending_columns[index % 2]:
                st.markdown(
                    f'<div class="person-row"><span class="person-avatar">{html.escape(initial)}</span>'
                    f'<span class="person-meta"><strong>{html.escape(participant.name)}</strong></span></div>',
                    unsafe_allow_html=True,
                )


def _show_overview(event: Event, user: User, users, _, admin_view: bool):
    if not event.is_started:
        _show_waiting_card(event, _)
        if admin_view:
            _show_start_section(event, _)
    else:
        if admin_view:
            _show_progress(event, _)
            _show_pending_participants(event, users, _)
        assignment = WichtelLogic.get_assignment_for_user(event, user.id)
        if assignment:
            _show_reveal(event, user, users, _, assignment)
        elif not admin_view:
            st.info(_("not_participant"))


def show_event_details(event: Event, user: User, _, admin_view: bool = False):
    """Detailseite mit kontextgebundener Navigation für Admins und Teilnehmer."""
    if admin_view:
        LinkAuthService.ensure_links_for_event(event)

    users = DataManager.load_users()

    title_html = (
        f'<div class="event-title-row"><div class="event-hero-title">{html.escape(event.title)}</div>'
        f'{_status_pill(event.is_started, _)}</div>'
    )
    if admin_view:
        with st.container(horizontal=True, vertical_alignment="center", gap="small", wrap=False, key="event-heading"):
            if st.button("←", key=f"back_{event.id}", help=_("back_to_list"), type="tertiary"):
                st.session_state.pop(f"confirm_start_{event.id}", None)
                st.session_state.current_event = None
                if "event" in st.query_params:
                    del st.query_params["event"]
                st.rerun()
            st.markdown(title_html, unsafe_allow_html=True, width="stretch")
    else:
        st.markdown(title_html, unsafe_allow_html=True)

    if event.description:
        st.markdown(
            f'<p class="event-description">{html.escape(event.description)}</p>',
            unsafe_allow_html=True,
        )

    if admin_view:
        overview_tab, invites_tab, edit_tab = st.tabs(
            [_("tab_overview"), _("tab_invites"), _("tab_edit")],
            on_change="rerun",
        )
        if overview_tab.open:
            with overview_tab:
                overview_main, overview_side = st.columns([2, 1], gap="large")
                with overview_main:
                    _show_overview(event, user, users, _, admin_view=True)
                with overview_side:
                    _show_details_card(event, users, _, admin_view=True)
        if invites_tab.open:
            with invites_tab:
                _show_send_invites(event, _)
                st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
                _show_invite_links(event, users, _)
        if edit_tab.open:
            with edit_tab:
                edit_main, edit_side = st.columns([2, 1], gap="large")
                with edit_main:
                    _show_edit_event(event, user, users, _)
                with edit_side:
                    _show_delete_event(event, _)
    else:
        _show_overview(event, user, users, _, admin_view=False)
        st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
        _show_details_card(event, users, _, admin_view=False, wide=True)
