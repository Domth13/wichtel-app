"""
Geschäftslogik für die Wichtel-App
"""
import random
from typing import List, Optional
from models import Event, Assignment, DataManager, User


class WichtelLogic:
    """Logik für Wichtel-Zuweisungen und Event-Management"""
    
    @staticmethod
    def assign_wichtel_random(event: Event) -> Event:
        """
        Weist jedem Teilnehmer zufällig einen anderen Teilnehmer zu
        Niemand kann sich selbst zugewiesen bekommen
        """
        participants = event.participant_ids.copy()
        receivers = participants.copy()
        
        # Mische die Empfänger
        random.shuffle(receivers)
        
        # Stelle sicher, dass niemand sich selbst bekommt
        for i, giver in enumerate(participants):
            if giver == receivers[i]:
                # Tausche mit dem nächsten
                next_idx = (i + 1) % len(receivers)
                receivers[i], receivers[next_idx] = receivers[next_idx], receivers[i]
        
        # Erstelle Zuweisungen
        event.assignments = [
            Assignment(giver_id=giver, receiver_id=receiver)
            for giver, receiver in zip(participants, receivers)
        ]
        event.is_started = True
        
        # Speichere Event (funktioniert mit JSON und MongoDB)
        try:
            # MongoDB hat update_event
            DataManager.update_event(event)
        except AttributeError:
            # JSON-Fallback
            events = DataManager.load_events()
            events[event.id] = event
            DataManager.save_events(events)
        
        return event
    
    @staticmethod
    def get_assignment_for_user(event: Event, user_id: str) -> Optional[Assignment]:
        """Findet die Zuweisung für einen bestimmten Benutzer"""
        for assignment in event.assignments:
            if assignment.giver_id == user_id:
                return assignment
        return None
    
    @staticmethod
    def get_receiver_name(assignment: Assignment) -> str:
        """Gibt den Namen des Empfängers zurück"""
        users = DataManager.load_users()
        receiver = users.get(assignment.receiver_id)
        return receiver.name if receiver else "Unbekannt"
    
    @staticmethod
    def reveal_assignment(event: Event, user_id: str):
        """Markiert eine Zuweisung als aufgedeckt"""
        for assignment in event.assignments:
            if assignment.giver_id == user_id:
                assignment.revealed = True
                break
        
        # Speichere Event (funktioniert mit JSON und MongoDB)
        try:
            # MongoDB hat update_event
            DataManager.update_event(event)
        except AttributeError:
            # JSON-Fallback
            events = DataManager.load_events()
            events[event.id] = event
            DataManager.save_events(events)
    
    @staticmethod
    def get_all_assignments_with_names(event: Event) -> List[dict]:
        """Gibt alle Zuweisungen mit Namen zurück"""
        users = DataManager.load_users()
        result = []
        
        for assignment in event.assignments:
            giver = users.get(assignment.giver_id)
            receiver = users.get(assignment.receiver_id)
            result.append({
                'giver': giver.name if giver else "Unbekannt",
                'receiver': receiver.name if receiver else "Unbekannt",
                'revealed': assignment.revealed
            })
        
        return result
    
    @staticmethod
    def can_user_access_event(event: Event, user_id: str) -> bool:
        """Prüft, ob ein Benutzer Zugriff auf ein Event hat"""
        return user_id in event.participant_ids or user_id == event.created_by
    
    @staticmethod
    def get_user_events(user_id: str) -> List[Event]:
        """Gibt alle Events zurück, an denen ein Benutzer teilnimmt"""
        # MongoDB hat optimierte Methode
        try:
            return DataManager.get_events_by_participant(user_id)
        except AttributeError:
            # JSON-Fallback
            events = DataManager.load_events()
            user_events = []
            
            for event in events.values():
                if WichtelLogic.can_user_access_event(event, user_id):
                    user_events.append(event)
            
            return sorted(user_events, key=lambda e: e.created_at, reverse=True)