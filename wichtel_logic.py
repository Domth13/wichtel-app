"""
Geschäftslogik für die Wichtel-App.
"""
import random
from typing import List, Optional

from models import Assignment, DataManager, Event


class WichtelLogic:
    """Logik für Wichtel-Zuweisungen und Event-Management."""

    @staticmethod
    def assign_wichtel_random(event: Event) -> Event:
        """
        Weist jedem Teilnehmer zufällig einen anderen Teilnehmer zu.
        Niemand bekommt sich selbst, und jede Person wird genau einmal beschenkt.
        """
        participants = list(event.participant_ids)
        if len(participants) != len(set(participants)):
            raise ValueError("duplicate_participants")
        if len(participants) < 2:
            raise ValueError("min_two_participants")

        receivers = participants.copy()
        for _ in range(200):
            random.shuffle(receivers)
            if all(giver != receiver for giver, receiver in zip(participants, receivers)):
                break
        else:
            # Deterministische Rotation als garantierter Fallback.
            receivers = participants[1:] + participants[:1]

        event.assignments = [
            Assignment(giver_id=giver, receiver_id=receiver)
            for giver, receiver in zip(participants, receivers)
        ]
        event.is_started = True
        DataManager.update_event_fields(event, ("assignments", "is_started"))
        return event

    @staticmethod
    def get_assignment_for_user(event: Event, user_id: str) -> Optional[Assignment]:
        for assignment in event.assignments:
            if assignment.giver_id == user_id:
                return assignment
        return None

    @staticmethod
    def get_receiver_name(assignment: Assignment) -> str:
        users = DataManager.load_users()
        receiver = users.get(assignment.receiver_id)
        return receiver.name if receiver else "Unbekannt"

    @staticmethod
    def reveal_assignment(event: Event, user_id: str):
        """Markiert eine Zuweisung atomar als aufgedeckt."""
        DataManager.mark_revealed(event.id, user_id)
        for assignment in event.assignments:
            if assignment.giver_id == user_id:
                assignment.revealed = True
                break

    @staticmethod
    def get_all_assignments_with_names(event: Event) -> List[dict]:
        users = DataManager.load_users()
        result = []
        for assignment in event.assignments:
            giver = users.get(assignment.giver_id)
            receiver = users.get(assignment.receiver_id)
            result.append(
                {
                    "giver": giver.name if giver else "Unbekannt",
                    "receiver": receiver.name if receiver else "Unbekannt",
                    "revealed": assignment.revealed,
                }
            )
        return result

    @staticmethod
    def can_user_access_event(event: Event, user_id: str) -> bool:
        return user_id in event.participant_ids or user_id == event.created_by

    @staticmethod
    def get_user_events(user_id: str) -> List[Event]:
        return DataManager.get_events_by_participant(user_id)
