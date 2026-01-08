from repositories.club_repository import ClubRepository
from typing import List, Dict

class ClubService:
    """Serwis dla klubów"""
    
    def __init__(self):
        self.club_repo = ClubRepository()
    
    def get_all(self) -> List[Dict]:
        """Pobiera listę wszystkich klubów"""
        return self.club_repo.get_all()
    
    def exists(self, club_name: str) -> bool:
        """Sprawdza czy klub istnieje"""
        return self.club_repo.exists(club_name)


