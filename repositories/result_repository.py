from database import get_conn
from config import SCHEMA
from typing import Optional, Dict

class ResultRepository:
    """Repozytorium dla wyników - wszystkie zapytania SQL identyczne jak wcześniej"""
    
    def find_by_athlete_event_category(self, athlete_code: str, event_id: int, category_name: str) -> Optional[Dict]:
        """
        Znajduje wynik zawodnika dla eventu i kategorii.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT place, points
                FROM {SCHEMA}.results
                WHERE athlete_code = %s 
                  AND event_id = %s 
                  AND category_name = %s
                LIMIT 1
            """, (athlete_code, event_id, category_name))
            row = cur.fetchone()
            if row:
                return {"place": row[0], "points": row[1]}
            return None


