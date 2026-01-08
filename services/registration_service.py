from repositories.registration_repository import RegistrationRepository
from repositories.user_repository import UserRepository
from repositories.category_repository import CategoryRepository
from repositories.result_repository import ResultRepository
from typing import Dict, List

class RegistrationService:
    """Serwis dla rejestracji na zawody"""
    
    def __init__(self):
        self.registration_repo = RegistrationRepository()
        self.user_repo = UserRepository()
        self.category_repo = CategoryRepository()
        self.result_repo = ResultRepository()
    
    def get_my_registration(self, user_id: int) -> Dict:
        """
        Pobiera rejestracje użytkownika.
        """
        athlete_code = self.user_repo.get_athlete_code(user_id)
        if not athlete_code:
            return {"error": "Nie masz przypisanego kodu zawodnika."}
        
        rows = self.registration_repo.find_by_athlete_code_view(athlete_code)
        
        registrations = []
        for row in rows:
            reg_id, event_id, category_kata_id, category_kumite_id = row[0], row[1], row[2], row[3]
            
            # Pobierz wyniki dla Kata
            kata_result = None
            if category_kata_id:
                kata_category_name = self.category_repo.get_kata_name(category_kata_id)
                if kata_category_name:
                    kata_result = self.result_repo.find_by_athlete_event_category(
                        athlete_code, event_id, kata_category_name
                    )
            
            # Pobierz wyniki dla Kumite
            kumite_result = None
            if category_kumite_id:
                kumite_category_name = self.category_repo.get_kumite_name(category_kumite_id)
                if kumite_category_name:
                    kumite_result = self.result_repo.find_by_athlete_event_category(
                        athlete_code, event_id, kumite_category_name
                    )
            
            registrations.append({
                "reg_id": reg_id,
                "event_id": event_id,
                "category_kata_id": category_kata_id,
                "category_kumite_id": category_kumite_id,
                "event_name": row[4],
                "start_date": row[5].isoformat() if row[5] else None,
                "end_date": row[6].isoformat() if row[6] else None,
                "kata_name": row[7],
                "kumite_name": row[8],
                "kata_result": kata_result,
                "kumite_result": kumite_result
            })
        
        return {"registrations": registrations}
    
    def withdraw(self, user_id: int, registration_id: int) -> Dict:
        """
        Wycofuje całkowicie zgłoszenie.
        """
        athlete_code = self.user_repo.get_athlete_code(user_id)
        if not athlete_code:
            return {"error": "Nie masz przypisanego kodu zawodnika."}
        
        # Weryfikacja przynależności
        reg = self.registration_repo.find_by_id_and_athlete_simple(registration_id, athlete_code)
        if not reg:
            return {"error": "Nie znaleziono zgłoszenia lub nie masz uprawnień do jego usunięcia."}
        
        self.registration_repo.delete(registration_id, athlete_code)
        return {"success": True, "message": "Twoje zgłoszenie zostało wycofane."}
    
    def withdraw_discipline(self, user_id: int, registration_id: int, discipline_type: str) -> Dict:
        """
        Wycofuje pojedynczą dyscyplinę z rejestracji.
        """
        if discipline_type not in ("kata", "kumite"):
            return {"error": "Nieprawidłowy typ dyscypliny."}
        
        athlete_code = self.user_repo.get_athlete_code(user_id)
        if not athlete_code:
            return {"error": "Nie masz przypisanego kodu zawodnika."}
        
        # Weryfikacja istnienia zgłoszenia
        reg = self.registration_repo.find_by_id_and_athlete(registration_id, athlete_code)
        if not reg:
            return {"error": "Nie masz aktywnego zgłoszenia lub nie masz uprawnień."}
        
        reg_id, kata_id, kumite_id = reg
        
        try:
            message = self.registration_repo.update_discipline_transaction(reg_id, discipline_type, kata_id, kumite_id)
            return {"success": True, "message": message}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Błąd podczas wycofywania dyscypliny: {e}"}

