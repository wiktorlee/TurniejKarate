from repositories.competition_repository import CompetitionRepository
from repositories.bracket_repository import BracketRepository
from repositories.user_repository import UserRepository
from typing import Dict, List, Optional

class CompetitionService:
    """Serwis dla zawodów (Kata, Kumite)"""
    
    def __init__(self):
        self.competition_repo = CompetitionRepository()
        self.bracket_repo = BracketRepository()
        self.user_repo = UserRepository()
    
    def get_kata_competitors(self, user_id: int, event_id: int, category_kata_id: int) -> Dict:
        """Pobiera listę zawodników Kata."""
        user_athlete_code = self.user_repo.get_athlete_code(user_id)
        
        event_cat = self.competition_repo.get_kata_event_info(event_id, category_kata_id)
        if not event_cat:
            return {"error": "Nie znaleziono eventu lub kategorii."}
        
        event_name, start_date, end_date, category_name = event_cat
        
        competitors = self.competition_repo.get_kata_competitors(event_id, category_kata_id)
        
        competitors_list = []
        for row in competitors:
            is_current_user = (row[0] == user_athlete_code)
            competitors_list.append({
                "athlete_code": row[0],
                "first_name": row[1] or "",
                "last_name": row[2] or "",
                "country_code": row[3],
                "club_name": row[4] or "",
                "nationality": row[5] or "",
                "place": row[6],
                "points": row[7],
                "is_current_user": is_current_user
            })
        
        return {
            "event_name": event_name,
            "category_name": category_name,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "competitors": competitors_list,
            "event_id": event_id
        }
    
    def get_kumite_bracket(self, user_id: int, event_id: int, category_kumite_id: int) -> Dict:
        """Pobiera drzewko walk Kumite."""
        user_athlete_code = self.user_repo.get_athlete_code(user_id)
        
        event_cat = self.competition_repo.get_kumite_event_info(event_id, category_kumite_id)
        if not event_cat:
            return {"error": "Nie znaleziono eventu lub kategorii."}
        
        event_name, start_date, end_date, category_name = event_cat
        
        # Pobierz listę zarejestrowanych zawodników
        registered_athletes = self.competition_repo.get_kumite_competitors(event_id, category_kumite_id)
        
        # Sprawdź czy istnieją pojedynki
        fights_count = self.bracket_repo.count_fights(category_kumite_id, event_id, 1)
        
        # Pobierz listę zawodników w drzewku
        athletes_in_bracket = set()
        if fights_count > 0:
            athletes_in_bracket = self.bracket_repo.get_athletes_in_bracket(category_kumite_id, event_id, 1)
        
        # Wygeneruj/odśwież drzewka jeśli potrzeba
        if fights_count == 0 or registered_athletes != athletes_in_bracket:
            if fights_count > 0:
                self.bracket_repo.delete_round(category_kumite_id, event_id, 1)
            
            if len(registered_athletes) >= 2:
                athletes = self.competition_repo.get_athletes_for_bracket(event_id, category_kumite_id)
                self.bracket_repo.generate_bracket_transaction(event_id, category_kumite_id, athletes)
                fights_count = self.bracket_repo.count_fights(category_kumite_id, event_id, 1)
        
        # Pobierz wszystkie rundy
        fights = self.bracket_repo.get_bracket_with_users(category_kumite_id, event_id)
        
        fights_list = []
        for row in fights:
            fight_no, red_code, blue_code = row[1], row[2], row[3]
            is_user_in_fight = (red_code == user_athlete_code or blue_code == user_athlete_code)
            
            fights_list.append({
                "fight_no": fight_no,
                "red_code": red_code,
                "blue_code": blue_code,
                "red_name": f"{row[4] or ''} {row[5] or ''}".strip() if row[4] or row[5] else "BYE",
                "red_country": row[6] or "",
                "red_club": row[7] or "",
                "blue_name": f"{row[8] or ''} {row[9] or ''}".strip() if row[8] or row[9] else "BYE",
                "blue_country": row[10] or "",
                "blue_club": row[11] or "",
                "winner_code": row[12],
                "red_score": row[13],
                "blue_score": row[14],
                "is_finished": row[15] if row[15] is not None else False,
                "is_bye": (blue_code is None),
                "is_current_user": is_user_in_fight
            })
        
        return {
            "event_name": event_name,
            "category_name": category_name,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "fights_list": fights_list,
            "event_id": event_id,
            "category_kumite_id": category_kumite_id
        }

