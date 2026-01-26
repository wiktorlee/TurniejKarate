from database import get_conn
from config import SCHEMA
from typing import List, Dict

class EventRepository:
    """Repozytorium dla eventów"""
    
    def find_active(self) -> List[Dict]:
        """Znajduje aktywne eventy."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id, name FROM {SCHEMA}.events WHERE is_active = true ORDER BY start_date, name")
            return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]


