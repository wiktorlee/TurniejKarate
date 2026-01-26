from database import get_conn
from config import SCHEMA
from typing import List, Dict

class ClubRepository:
    """Repozytorium dla klubów"""
    
    def get_all(self) -> List[Dict]:
        """Pobiera listę wszystkich klubów."""
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(f"SELECT name, city FROM {SCHEMA}.clubs ORDER BY name")
                return [{"name": r[0], "city": r[1]} for r in cur.fetchall()]
        except Exception:
            return []
    
    def exists(self, club_name: str) -> bool:
        """Sprawdza czy klub istnieje."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT name FROM {SCHEMA}.clubs WHERE name = %s", (club_name,))
            return cur.fetchone() is not None


