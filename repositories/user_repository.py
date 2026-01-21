from database import get_conn
from config import SCHEMA
from typing import Optional, Dict
import psycopg.errors

class UserRepository:
    """Repozytorium dla użytkowników - wszystkie zapytania SQL identyczne jak wcześniej"""
    
    def find_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Znajduje użytkownika po ID.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, login, country_code, nationality, club_name, first_name, last_name, sex, birth_date, weight, athlete_code
                FROM {SCHEMA}.users
                WHERE id=%s
            """, (user_id,))
            row = cur.fetchone()
            
            if not row:
                return None
            
            return {
                "id": row[0],
                "login": row[1],
                "country_code": row[2],
                "nationality": row[3],
                "club_name": row[4],
                "first_name": row[5],
                "last_name": row[6],
                "sex": row[7],
                "birth_date": row[8],
                "weight": row[9],
                "athlete_code": row[10],
            }
    
    def find_by_login(self, login: str, password: str) -> Optional[Dict]:
        """
        Znajduje użytkownika po loginie i haśle.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id, is_admin FROM {SCHEMA}.users WHERE login=%s AND password=%s", (login, password))
            row = cur.fetchone()
            
            if not row:
                return None
            
            return {"id": row[0], "is_admin": row[1] if row[1] else False}
    
    def create(self, user_data: dict) -> int:
        """
        Tworzy nowego użytkownika.
        SQL IDENTYCZNE jak wcześniej!
        Zwraca ID utworzonego użytkownika.
        """
        insert_sql = f"""
            INSERT INTO {SCHEMA}.users
            (login, password, country_code, nationality, club_name, first_name, last_name, sex, birth_date, weight)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(insert_sql, (
                user_data["login"],
                user_data["password"],
                user_data["country_code"],
                user_data["nationality"],
                user_data["club_name"],
                user_data["first_name"],
                user_data["last_name"],
                user_data["sex"],
                user_data["birth_date"],
                user_data["weight"]
            ))
            conn.commit()
            return cur.fetchone()[0]
    
    def update(self, user_id: int, user_data: dict) -> None:
        """
        Aktualizuje dane użytkownika.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            if user_data.get("password"):
                # Aktualizacja z hasłem
                update_sql = f"""
                    UPDATE {SCHEMA}.users
                    SET country_code = %s, nationality = %s, club_name = %s,
                        first_name = %s, last_name = %s, sex = %s,
                        birth_date = %s, weight = %s, password = %s
                    WHERE id = %s
                """
                cur.execute(update_sql, (
                    user_data["country_code"],
                    user_data["nationality"],
                    user_data["club_name"],
                    user_data["first_name"],
                    user_data["last_name"],
                    user_data["sex"],
                    user_data["birth_date"],
                    user_data["weight"],
                    user_data["password"],
                    user_id
                ))
            else:
                # Aktualizacja bez hasła
                update_sql = f"""
                    UPDATE {SCHEMA}.users
                    SET country_code = %s, nationality = %s, club_name = %s,
                        first_name = %s, last_name = %s, sex = %s,
                        birth_date = %s, weight = %s
                    WHERE id = %s
                """
                cur.execute(update_sql, (
                    user_data["country_code"],
                    user_data["nationality"],
                    user_data["club_name"],
                    user_data["first_name"],
                    user_data["last_name"],
                    user_data["sex"],
                    user_data["birth_date"],
                    user_data["weight"],
                    user_id
                ))
            conn.commit()
    
    def is_admin(self, user_id: int) -> bool:
        """
        Sprawdza czy użytkownik jest administratorem.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT is_admin FROM {SCHEMA}.users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] else False
    
    def get_athlete_code(self, user_id: int) -> Optional[str]:
        """
        Pobiera kod zawodnika użytkownika.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return row[0] if row and row[0] else None
    
    def get_athlete_data(self, user_id: int) -> Optional[Dict]:
        """
        Pobiera dane zawodnika (athlete_code, sex, birth_date, weight).
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code, sex, birth_date, weight FROM {SCHEMA}.users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "athlete_code": row[0],
                "sex": row[1],
                "birth_date": row[2],
                "weight": row[3]
            }


