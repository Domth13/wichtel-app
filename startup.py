"""Vorbereitung der Daten beim ersten Öffnen eines Teilnehmerlinks."""

from concurrent.futures import ThreadPoolExecutor


def prepare_link_storage(ensure_admin, load_events):
    """Lädt unabhängige Daten parallel und gibt Fehler beider Zugriffe weiter."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        events_future = executor.submit(load_events)
        ensure_admin()
        events_future.result()
