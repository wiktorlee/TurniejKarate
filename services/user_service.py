from repositories.user_repository import UserRepository
from repositories.club_repository import ClubRepository
from datetime import date
from typing import Dict, Optional

class UserService:
    """Serwis dla użytkowników"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.club_repo = ClubRepository()
    
    def get_profile(self, user_id: int) -> Dict:
        """
        Pobiera profil użytkownika.
        Zwraca dict z danymi użytkownika i listą klubów.
        """
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return {"error": "Użytkownik nie istnieje."}
        
        # Formatowanie daty dla JSON
        user_dict = {
            "id": user["id"],
            "login": user["login"],
            "country_code": user["country_code"],
            "nationality": user["nationality"],
            "club_name": user["club_name"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "sex": user["sex"],
            "birth_date": user["birth_date"].isoformat() if user["birth_date"] else None,
            "weight": float(user["weight"]) if user["weight"] else None,
            "athlete_code": user["athlete_code"],
        }
        
        clubs = self.club_repo.get_all()
        
        return {
            "user": user_dict,
            "clubs": clubs
        }
    
    def update_profile(self, user_id: int, data: Dict) -> Dict:
        """
        Aktualizuje profil użytkownika.
        Zwraca dict z success/error.
        """
        errors = []
        
        country = (data.get("country_code") or "").strip().upper()
        nationality = (data.get("nationality") or "").strip()
        club_name = (data.get("club_name") or "").strip()
        first = (data.get("first_name") or "").strip()
        last = (data.get("last_name") or "").strip()
        sex = (data.get("sex") or "").strip().upper()
        birth_raw = (data.get("birth_date") or "").strip()
        weight_raw = (data.get("weight") or "").strip()
        password = (data.get("password") or "").strip()
        
        # Walidacja
        if len(country) != 3:
            errors.append("Kod kraju musi mieć 3 litery (np. POL).")
        if not nationality:
            errors.append("Podaj narodowość.")
        if not club_name:
            errors.append("Wybierz klub.")
        if sex not in ("M", "F"):
            errors.append("Płeć musi być M lub F.")
        
        # Walidacja daty urodzenia
        birth_date = None
        if birth_raw:
            try:
                y, m, d = map(int, birth_raw.split("-"))
                birth_date = date(y, m, d)
                if birth_date > date.today():
                    errors.append("Data urodzenia nie może być w przyszłości.")
            except Exception:
                errors.append("Niepoprawny format daty (YYYY-MM-DD).")
        else:
            errors.append("Data urodzenia jest wymagana.")
        
        # Walidacja wagi
        weight = None
        if weight_raw:
            try:
                weight = float(weight_raw)
                if weight <= 0:
                    errors.append("Waga musi być dodatnia.")
            except ValueError:
                errors.append("Niepoprawny format wagi.")
        else:
            errors.append("Podaj wagę.")
        
        # Weryfikacja istnienia klubu
        if club_name and not self.club_repo.exists(club_name):
            errors.append("Wybrany klub nie istnieje.")
        
        if errors:
            return {"error": errors[0], "errors": errors}
        
        # Aktualizacja użytkownika
        user_data = {
            "country_code": country,
            "nationality": nationality,
            "club_name": club_name,
            "first_name": first,
            "last_name": last,
            "sex": sex,
            "birth_date": birth_date,
            "weight": weight
        }
        
        if password:
            user_data["password"] = password
        
        try:
            self.user_repo.update(user_id, user_data)
            return {"success": True, "message": "Profil został zaktualizowany!"}
        except Exception as e:
            return {"error": f"Błąd podczas aktualizacji profilu: {e}"}
    
    def get_athlete_code(self, user_id: int) -> Optional[str]:
        """Pobiera kod zawodnika użytkownika"""
        return self.user_repo.get_athlete_code(user_id)
    
    def get_athlete_data(self, user_id: int) -> Optional[Dict]:
        """Pobiera dane zawodnika"""
        return self.user_repo.get_athlete_data(user_id)
    
    def is_admin(self, user_id: int) -> bool:
        """Sprawdza czy użytkownik jest administratorem"""
        return self.user_repo.is_admin(user_id)


