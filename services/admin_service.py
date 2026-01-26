from repositories.admin_repository import AdminRepository
from typing import Dict

class AdminService:
    """Serwis dla operacji admina"""
    
    def __init__(self):
        self.admin_repo = AdminRepository()
    
    def get_dashboard(self) -> Dict:
        """
        Pobiera dane do panelu admina.
        Zwraca dict z statusem systemu i statystykami.
        """
        system_status = self.admin_repo.get_system_status()
        statistics = self.admin_repo.get_statistics()
        
        # Formatowanie dat dla JSON
        if system_status.get("simulation_date"):
            system_status["simulation_date"] = system_status["simulation_date"].isoformat()
        if system_status.get("reset_date"):
            system_status["reset_date"] = system_status["reset_date"].isoformat()
        if system_status.get("updated_at"):
            system_status["updated_at"] = system_status["updated_at"].isoformat()
        
        return {
            "system_status": system_status,
            **statistics
        }
    
    def simulate_season(self) -> Dict:
        """Symuluje sezon zawodów."""
        system_status = self.admin_repo.get_system_status()
        if system_status["status"] == "SIMULATED":
            return {"error": "System jest już w stanie zasymulowanym. Najpierw wykonaj reset."}
        
        results = self.admin_repo.call_simulate_competitions()
        
        if not results:
            return {"error": "Symulacja nie zwróciła wyników. Sprawdź czy są aktywne eventy i rejestracje."}
        
        message = results[0][0] if results[0][0] else "Symulacja zakończona"
        events_processed = results[0][1] if len(results[0]) > 1 else 0
        results_created = results[0][2] if len(results[0]) > 2 else 0
        
        # Aktualizacja statusu
        self.admin_repo.update_system_status("SIMULATED")
        
        return {
            "success": True,
            "message": f"Symulacja zakończona! {message}. Przetworzono {events_processed} eventów, utworzono {results_created} wyników."
        }
    
    def reset_system(self, restore_dummies: bool) -> Dict:
        """
        Resetuje system.
        """
        result = self.admin_repo.reset_system(restore_dummies)
        
        msg = f"System zresetowany. Usunięto {result['deleted_results']} wyników i {result['deleted_fights']} walk."
        if restore_dummies:
            msg += f" Przywrócono {result['restored_count']} rejestracji kukiełek."
        else:
            msg += " (Rejestracje kukiełek nie zostały przywrócone - użyj przycisku 'Zarejestruj kukiełki' jeśli potrzebujesz)"
        
        return {"success": True, "message": msg}
    
    def restore_dummy_athletes(self) -> Dict:
        """Przywraca rejestracje kukiełek."""
        results = self.admin_repo.call_restore_dummy_athletes()
        
        total_registrations = sum(row[2] for row in results if isinstance(row[2], int)) if results else 0
        athletes_processed = len([r for r in results if r[2] and r[2] > 0]) if results else 0
        
        if total_registrations > 0:
            return {
                "success": True,
                "message": f"Pomyślnie zarejestrowano {total_registrations} zapisów dla {athletes_processed} kukiełek."
            }
        else:
            if results and results[0][0] == 'Brak kukiełek do zarejestrowania':
                message = "Brak kukiełek do zarejestrowania. Upewnij się, że istnieją użytkownicy z is_dummy=true i przypisanymi kategoriami."
            else:
                message = "Brak nowych rejestracji do utworzenia. (Wszystkie kukiełki mogą być już zarejestrowane lub brak aktywnych eventów)"
            return {
                "success": True,
                "message": message,
                "info": True
            }


