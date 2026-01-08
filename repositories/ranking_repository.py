from database import get_conn
from config import SCHEMA
from typing import List, Tuple

class RankingRepository:
    """
    Repozytorium dla rankingów - używa widoku SQL z Supabase.
    Wszystkie zapytania SQL IDENTYCZNE jak wcześniej!
    Widok v_results_with_users z Supabase - BEZ ZMIAN!
    """
    
    def get_club_ranking(self) -> List[Tuple]:
        """
        Pobiera ranking klubowy.
        SQL IDENTYCZNE jak wcześniej!
        Widok v_results_with_users z Supabase - BEZ ZMIAN!
        Zwraca listę krotek: (club_name, total_points)
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT club_name, SUM(points) as total_points
                FROM {SCHEMA}.v_results_with_users
                WHERE club_name IS NOT NULL AND club_name != ''
                GROUP BY club_name
                ORDER BY total_points DESC
            """)
            return cur.fetchall()
    
    def get_nation_ranking(self) -> List[Tuple]:
        """
        Pobiera ranking narodowościowy.
        SQL IDENTYCZNE jak wcześniej!
        Widok v_results_with_users z Supabase - BEZ ZMIAN!
        Zwraca listę krotek: (country_code, total_points)
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT country_code, SUM(points) as total_points
                FROM {SCHEMA}.v_results_with_users
                WHERE country_code IS NOT NULL
                GROUP BY country_code
                ORDER BY total_points DESC
            """)
            return cur.fetchall()
    
    def get_individual_ranking(self) -> List[Tuple]:
        """
        Pobiera ranking indywidualny per kategoria.
        SQL IDENTYCZNE jak wcześniej!
        Widok v_results_with_users z Supabase - BEZ ZMIAN!
        Zwraca listę krotek: (category_name, first_name, last_name, club_name, country_code, total_points)
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT category_name, 
                       first_name, last_name, club_name, country_code,
                       SUM(points) as total_points
                FROM {SCHEMA}.v_results_with_users
                GROUP BY category_name, athlete_code, first_name, last_name, club_name, country_code
                ORDER BY category_name ASC, total_points DESC
            """)
            return cur.fetchall()


