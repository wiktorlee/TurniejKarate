from database import get_conn
from config import SCHEMA
from typing import List, Tuple, Set, Optional

class BracketRepository:
    """
    Repozytorium dla drzewek walk (draw_fight).
    Wszystkie zapytania SQL IDENTYCZNE jak wcześniej!
    """
    
    def count_fights(self, category_kumite_id: int, event_id: int, round_no: int = 1) -> int:
        """
        Liczy walki w rundzie.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*) FROM {SCHEMA}.draw_fight 
                WHERE category_kumite_id = %s AND event_id = %s AND round_no = %s
            """, (category_kumite_id, event_id, round_no))
            return cur.fetchone()[0]
    
    def get_athletes_in_bracket(self, category_kumite_id: int, event_id: int, round_no: int = 1) -> Set[str]:
        """
        Pobiera listę zawodników w drzewku.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT red_code, blue_code
                FROM {SCHEMA}.draw_fight
                WHERE category_kumite_id = %s AND event_id = %s AND round_no = %s
            """, (category_kumite_id, event_id, round_no))
            athletes = set()
            for row in cur.fetchall():
                if row[0]:
                    athletes.add(row[0])
                if row[1]:
                    athletes.add(row[1])
            return athletes
    
    def delete_round(self, category_kumite_id: int, event_id: int, round_no: int = 1) -> None:
        """Usuwa walki z rundy."""
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                cur.execute(f"""
                    DELETE FROM {SCHEMA}.draw_fight 
                    WHERE category_kumite_id = %s AND event_id = %s AND round_no = %s
                """, (category_kumite_id, event_id, round_no))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def create_fight(self, conn, cur, category_kumite_id: int, event_id: int, 
                     round_no: int, fight_no: int, red_code: Optional[str], blue_code: Optional[str]) -> None:
        """
        Tworzy walkę w ramach transakcji.
        SQL IDENTYCZNE jak wcześniej!
        """
        cur.execute(f"""
            INSERT INTO {SCHEMA}.draw_fight 
            (category_id, category_kumite_id, event_id, round_no, fight_no, red_code, blue_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (category_kumite_id, category_kumite_id, event_id, round_no, fight_no, red_code, blue_code))
    
    def get_bracket_with_users(self, category_kumite_id: int, event_id: int) -> List[Tuple]:
        """
        Pobiera drzewko walk z danymi zawodników.
        SQL IDENTYCZNE jak wcześniej!
        Zwraca listę krotek z danymi walk.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT df.round_no, df.fight_no, df.red_code, df.blue_code,
                       COALESCE(red_u.first_name, '') as red_first, 
                       COALESCE(red_u.last_name, '') as red_last,
                       red_u.country_code as red_country,
                       red_u.club_name as red_club,
                       COALESCE(blue_u.first_name, '') as blue_first,
                       COALESCE(blue_u.last_name, '') as blue_last,
                       blue_u.country_code as blue_country,
                       blue_u.club_name as blue_club,
                       df.winner_code, df.red_score, df.blue_score, 
                       COALESCE(df.is_finished, FALSE) as is_finished
                FROM {SCHEMA}.draw_fight df
                LEFT JOIN {SCHEMA}.users red_u ON df.red_code = red_u.athlete_code
                LEFT JOIN {SCHEMA}.users blue_u ON df.blue_code = blue_u.athlete_code
                WHERE df.category_kumite_id = %s AND df.event_id = %s
                ORDER BY df.round_no, df.fight_no
            """, (category_kumite_id, event_id))
            return cur.fetchall()
    
    def generate_bracket_with_transaction(self, conn, cur, event_id: int, category_kumite_id: int, athletes: List[Optional[str]]) -> None:
        """
        Generuje drzewko walk w ramach transakcji (używane gdy transakcja jest już otwarta).
        SQL IDENTYCZNE jak wcześniej!
        """
        if len(athletes) < 2:
            raise ValueError("Za mało zawodników do utworzenia drzewka (min. 2)")
        
        if len(athletes) % 2 != 0:
            athletes.append(None)
        
        fight_no = 1
        for i in range(0, len(athletes), 2):
            red_code = athletes[i]
            blue_code = athletes[i + 1] if i + 1 < len(athletes) else None
            
            cur.execute(f"""
                INSERT INTO {SCHEMA}.draw_fight 
                (category_id, category_kumite_id, event_id, round_no, fight_no, red_code, blue_code)
                VALUES (%s, %s, %s, 1, %s, %s, %s)
            """, (category_kumite_id, category_kumite_id, event_id, fight_no, red_code, blue_code))
            fight_no += 1
    
    def generate_bracket_transaction(self, event_id: int, category_kumite_id: int, athletes: List[str]) -> None:
        """
        Generuje drzewko walk (zarządza transakcją wewnątrz).
        SQL IDENTYCZNE jak wcześniej!
        """
        if len(athletes) < 2:
            raise ValueError("Za mało zawodników do utworzenia drzewka (min. 2)")
        
        if len(athletes) % 2 != 0:
            athletes.append(None)
        
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                fight_no = 1
                for i in range(0, len(athletes), 2):
                    red_code = athletes[i]
                    blue_code = athletes[i + 1] if i + 1 < len(athletes) else None
                    
                    cur.execute(f"""
                        INSERT INTO {SCHEMA}.draw_fight 
                        (category_id, category_kumite_id, event_id, round_no, fight_no, red_code, blue_code)
                        VALUES (%s, %s, %s, 1, %s, %s, %s)
                    """, (category_kumite_id, category_kumite_id, event_id, fight_no, red_code, blue_code))
                    fight_no += 1
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise

