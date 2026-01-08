from repositories.category_repository import CategoryRepository
from repositories.event_repository import EventRepository
from repositories.discipline_repository import DisciplineRepository
from repositories.registration_repository import RegistrationRepository
from repositories.user_repository import UserRepository
from repositories.admin_repository import AdminRepository
from datetime import date
from typing import Dict
import psycopg.errors

class CategoryService:
    """Serwis dla kategorii i rejestracji"""
    
    def __init__(self):
        self.category_repo = CategoryRepository()
        self.event_repo = EventRepository()
        self.discipline_repo = DisciplineRepository()
        self.registration_repo = RegistrationRepository()
        self.user_repo = UserRepository()
        self.admin_repo = AdminRepository()
    
    def get_categories(self, user_id: int) -> Dict:
        """
        Pobiera listę eventów, dyscyplin i kategorii dla użytkownika.
        """
        # Sprawdź status systemu
        system_status_data = self.admin_repo.get_system_status()
        system_status = system_status_data.get("status", "ACTIVE")
        if system_status != 'ACTIVE':
            return {
                "error": "System jest w stanie zakończonym. Zapisy są zablokowane.",
                "system_status": system_status
            }
        
        # Pobierz dane użytkownika
        athlete_data = self.user_repo.get_athlete_data(user_id)
        if not athlete_data or not athlete_data["athlete_code"]:
            return {"error": "Nie masz przypisanego kodu zawodnika."}
        
        athlete_code = athlete_data["athlete_code"]
        user_sex = athlete_data["sex"]
        
        # Pobierz eventy
        events = self.event_repo.find_active()
        
        # Pobierz dyscypliny
        disciplines = self.discipline_repo.get_all()
        
        # Pobierz kategorie Kata
        categories_kata = self.category_repo.find_kata_by_sex(user_sex)
        
        # Pobierz kategorie Kumite
        categories_kumite = self.category_repo.find_kumite_by_sex(user_sex)
        
        # Sprawdź czy ma rejestracje
        registration_count = self.registration_repo.count_by_athlete(athlete_code)
        has_registration = registration_count > 0
        
        return {
            "events": events,
            "disciplines": disciplines,
            "categories_kata": categories_kata,
            "categories_kumite": categories_kumite,
            "has_registration": has_registration
        }
    
    def register_to_category(self, user_id: int, data: Dict) -> Dict:
        """
        Rejestruje użytkownika na kategorię.
        """
        # Sprawdź status systemu
        system_status_data = self.admin_repo.get_system_status()
        system_status = system_status_data.get("status", "ACTIVE")
        if system_status != 'ACTIVE':
            return {"error": "System jest w stanie zakończonym. Zapisy są zablokowane."}
        
        event_id = data.get("event_id")
        discipline_kata = data.get("discipline_kata", False)
        discipline_kumite = data.get("discipline_kumite", False)
        category_kata_id = data.get("category_kata_id")
        category_kumite_id = data.get("category_kumite_id")
        
        # Walidacja
        if not event_id:
            return {"error": "Nie wybrano eventu."}
        if not discipline_kata and not discipline_kumite:
            return {"error": "Wybierz przynajmniej jedną dyscyplinę (Kata lub Kumite)."}
        if discipline_kata and not category_kata_id:
            return {"error": "Wybierz kategorię dla Kata."}
        if discipline_kumite and not category_kumite_id:
            return {"error": "Wybierz kategorię dla Kumite."}
        
        # Pobierz dane użytkownika
        athlete_data = self.user_repo.get_athlete_data(user_id)
        if not athlete_data or not athlete_data["athlete_code"]:
            return {"error": "Nie masz przypisanego kodu zawodnika."}
        
        athlete_code = athlete_data["athlete_code"]
        user_sex = athlete_data["sex"]
        birth_date = athlete_data["birth_date"]
        weight = athlete_data["weight"]
        
        # Walidacja wieku i wagi
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        # Walidacja Kata
        if discipline_kata:
            kata_cat = self.category_repo.find_kata_by_id(category_kata_id)
            if not kata_cat:
                return {"error": "Nie znaleziono kategorii Kata."}
            
            kata_name, kata_sex, kata_min_age, kata_max_age = kata_cat
            
            if user_sex != kata_sex:
                return {"error": f"Nie możesz zapisać się do kategorii Kata {kata_name} (inna płeć)."}
            if kata_min_age and age < kata_min_age:
                return {"error": f"Za młody do kategorii Kata {kata_name} ({age} lat, wymagane min {kata_min_age})."}
            if kata_max_age and age > kata_max_age:
                return {"error": f"Za stary do kategorii Kata {kata_name} ({age} lat, dopuszczalne max {kata_max_age})."}
        
        # Walidacja Kumite
        if discipline_kumite:
            kumite_cat = self.category_repo.find_kumite_by_id(category_kumite_id)
            if not kumite_cat:
                return {"error": "Nie znaleziono kategorii Kumite."}
            
            kumite_name, kumite_sex, kumite_min_age, kumite_max_age, kumite_min_weight, kumite_max_weight = kumite_cat
            
            if user_sex != kumite_sex:
                return {"error": f"Nie możesz zapisać się do kategorii Kumite {kumite_name} (inna płeć)."}
            if kumite_min_age and age < kumite_min_age:
                return {"error": f"Za młody do kategorii Kumite {kumite_name} ({age} lat, wymagane min {kumite_min_age})."}
            if kumite_max_age and age > kumite_max_age:
                return {"error": f"Za stary do kategorii Kumite {kumite_name} ({age} lat, dopuszczalne max {kumite_max_age})."}
            if kumite_min_weight and weight and weight < kumite_min_weight:
                return {"error": f"Za lekki na kategorię Kumite {kumite_name} (min {kumite_min_weight} kg)."}
            if kumite_max_weight and weight and weight > kumite_max_weight:
                return {"error": f"Za ciężki na kategorię Kumite {kumite_name} (max {kumite_max_weight} kg)."}
        
        # Sprawdź istniejącą rejestrację
        existing_reg_id = self.registration_repo.find_by_athlete_and_event(athlete_code, event_id)
        
        # Pobranie discipline_id
        discipline_id = None
        if discipline_kata and not discipline_kumite:
            discipline_id = self.discipline_repo.find_by_name("Kata")
        elif discipline_kumite and not discipline_kata:
            discipline_id = self.discipline_repo.find_by_name("Kumite")
        
        try:
            if existing_reg_id:
                # Aktualizacja istniejącego zgłoszenia
                self.registration_repo.update(existing_reg_id, discipline_id, 
                                             category_kata_id if discipline_kata else None,
                                             category_kumite_id if discipline_kumite else None)
                return {"success": True, "message": "Zgłoszenie na ten event zostało zaktualizowane!"}
            else:
                # Nowa rejestracja
                if discipline_kata and discipline_kumite:
                    # Dwie osobne rejestracje - transakcja
                    kata_discipline_id = self.discipline_repo.find_by_name("Kata")
                    kumite_discipline_id = self.discipline_repo.find_by_name("Kumite")
                    self.registration_repo.create_two_disciplines_transaction(
                        athlete_code, event_id, kata_discipline_id, category_kata_id,
                        kumite_discipline_id, category_kumite_id
                    )
                    return {"success": True, "message": "Zostałeś pomyślnie zapisany na zawody w obu dyscyplinach!"}
                else:
                    # Pojedyncza rejestracja
                    self.registration_repo.create(
                        athlete_code, event_id, discipline_id,
                        category_kata_id if discipline_kata else None,
                        category_kumite_id if discipline_kumite else None
                    )
                    return {"success": True, "message": "Zostałeś pomyślnie zapisany na zawody!"}
        except psycopg.errors.UniqueViolation:
            return {"error": "Jesteś już zapisany (UniqueViolation)."}
        except Exception as e:
            return {"error": f"Wystąpił błąd bazy danych: {e}"}

