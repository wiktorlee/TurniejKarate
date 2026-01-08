from database import get_conn
from config import SCHEMA
from typing import List, Dict, Optional

class DisciplineRepository:
    """Repozytorium dla dyscyplin - wszystkie zapytania SQL identyczne jak wcześniej"""
    
    def get_all(self) -> List[Dict]:
        """
        Pobiera wszystkie dyscypliny.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id, name FROM {SCHEMA}.disciplines ORDER BY name")
            return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    
    def find_by_name(self, name: str) -> Optional[int]:
        """
        Znajduje dyscyplinę po nazwie.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = %s LIMIT 1", (name,))
            row = cur.fetchone()
            return row[0] if row else None


