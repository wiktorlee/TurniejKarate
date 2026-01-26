from database import get_conn
from config import SCHEMA
from typing import List, Tuple, Optional, Set

class CompetitionRepository:
    """Repozytorium dla zawodów"""
    
    def get_kata_event_info(self, event_id: int, category_kata_id: int) -> Optional[Tuple]:
        """Pobiera informacje o evencie i kategorii Kata. Zwraca: (event_name, event_start_date, event_end_date, category_name) lub None"""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT event_name, event_start_date, event_end_date, category_name
                FROM {SCHEMA}.v_kata_competitors
                WHERE event_id = %s AND category_kata_id = %s
                LIMIT 1
            """, (event_id, category_kata_id))
            return cur.fetchone()
    
    def get_kata_competitors(self, event_id: int, category_kata_id: int) -> List[Tuple]:
        """Pobiera listę zawodników Kata. Zwraca listę krotek: (athlete_code, first_name, last_name, country_code, club_name, nationality, place, points)"""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT athlete_code, first_name, last_name, 
                       country_code, club_name, nationality,
                       place, points
                FROM {SCHEMA}.v_kata_competitors
                WHERE event_id = %s AND category_kata_id = %s
                ORDER BY 
                    CASE WHEN place IS NULL THEN 999 ELSE place END,
                    last_name, first_name, athlete_code
            """, (event_id, category_kata_id))
            return cur.fetchall()
    
    def get_kumite_event_info(self, event_id: int, category_kumite_id: int) -> Optional[Tuple]:
        """Pobiera informacje o evencie i kategorii Kumite. Zwraca: (event_name, event_start_date, event_end_date, category_name) lub None"""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT event_name, event_start_date, event_end_date, category_name
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
                LIMIT 1
            """, (event_id, category_kumite_id))
            return cur.fetchone()
    
    def get_kumite_competitors(self, event_id: int, category_kumite_id: int) -> Set[str]:
        """Pobiera listę kodów zawodników Kumite."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT athlete_code
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
            """, (event_id, category_kumite_id))
            return set(row[0] for row in cur.fetchall())
    
    def get_athletes_for_bracket(self, event_id: int, category_kumite_id: int) -> List[str]:
        """Pobiera zawodników do generowania drzewka (losowo)."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT athlete_code
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
                ORDER BY RANDOM()
            """, (event_id, category_kumite_id))
            return [row[0] for row in cur.fetchall()]


