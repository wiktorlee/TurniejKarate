from repositories.user_repository import UserRepository
from repositories.club_repository import ClubRepository
from datetime import date
import psycopg.errors
from typing import Dict

class AuthService:
    """Serwis dla autoryzacji"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.club_repo = ClubRepository()
    
    def login(self, login: str, password: str) -> Dict:
        """
        Loguje użytkownika.
        Zwraca dict z user_id i is_admin lub error.
        """
        if not login:
            return {"error": "Podaj login."}
        if not password:
            return {"error": "Podaj hasło."}
        
        user = self.user_repo.find_by_login(login, password)
        if not user:
            return {"error": "Błędny login lub hasło."}
        
        return {
            "success": True,
            "message": "Zalogowano.",
            "user_id": user["id"],
            "is_admin": user["is_admin"]
        }
    
    def register(self, data: Dict) -> Dict:
        """
        Rejestruje nowego użytkownika.
        Zwraca dict z success/error.
        """
        errors = []
        
        login = str(data.get("login") or "").strip()
        password = str(data.get("password") or "").strip()
        country = str(data.get("country_code") or "").strip().upper()
        nationality = str(data.get("nationality") or "").strip()
        club_name = str(data.get("club_name") or "").strip()
        first = str(data.get("first_name") or "").strip()
        last = str(data.get("last_name") or "").strip()
        sex = str(data.get("sex") or "").strip().upper()
        birth_raw = str(data.get("birth_date") or "").strip()
        weight_raw = data.get("weight")
        if weight_raw is not None:
            weight_raw = str(weight_raw).strip()
        else:
            weight_raw = ""
        
        # Walidacja
        if not login:
            errors.append("Podaj login.")
        if not password:
            errors.append("Podaj hasło.")
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
        
        # Tworzenie użytkownika
        user_data = {
            "login": login,
            "password": password,
            "country_code": country,
            "nationality": nationality,
            "club_name": club_name,
            "first_name": first,
            "last_name": last,
            "sex": sex,
            "birth_date": birth_date,
            "weight": weight
        }
        
        try:
            user_id = self.user_repo.create(user_data)
            return {
                "success": True,
                "message": "Konto utworzone.",
                "user_id": user_id
            }
        except psycopg.errors.UniqueViolation:
            return {"error": "Taki login już istnieje."}
        except Exception as e:
            return {"error": f"Błąd podczas rejestracji: {e}"}


