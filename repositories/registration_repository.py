from database import get_conn
from config import SCHEMA
from typing import List, Dict, Optional, Tuple

class RegistrationRepository:
    """Repozytorium dla rejestracji - wszystkie zapytania SQL identyczne jak wcześniej"""
    
    def count_by_athlete(self, athlete_code: str) -> int:
        """
        Liczy rejestracje zawodnika.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.registrations WHERE athlete_code=%s", (athlete_code,))
            return cur.fetchone()[0]
    
    def find_by_athlete_and_event(self, athlete_code: str, event_id: int) -> Optional[int]:
        """
        Znajduje rejestrację zawodnika na event.
        SQL IDENTYCZNE jak wcześniej!
        Zwraca ID rejestracji lub None.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE athlete_code=%s AND event_id=%s", (athlete_code, event_id))
            row = cur.fetchone()
            return row[0] if row else None
    
    def find_by_id_and_athlete(self, registration_id: int, athlete_code: str) -> Optional[Tuple]:
        """
        Znajduje rejestrację po ID i kodzie zawodnika.
        SQL IDENTYCZNE jak wcześniej!
        Zwraca: (id, category_kata_id, category_kumite_id) lub None
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id, category_kata_id, category_kumite_id FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            return cur.fetchone()
    
    def find_by_id_and_athlete_simple(self, registration_id: int, athlete_code: str) -> Optional[int]:
        """
        Sprawdza czy rejestracja należy do zawodnika.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            row = cur.fetchone()
            return row[0] if row else None
    
    def create(self, athlete_code: str, event_id: int, discipline_id: Optional[int], 
               category_kata_id: Optional[int], category_kumite_id: Optional[int]) -> None:
        """Tworzy nową rejestrację."""
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                cur.execute(f"""
                    INSERT INTO {SCHEMA}.registrations 
                    (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def create_with_transaction(self, conn, cur, athlete_code: str, event_id: int, 
                                discipline_id: Optional[int], category_kata_id: Optional[int], 
                                category_kumite_id: Optional[int]) -> None:
        """
        Tworzy rejestrację w ramach transakcji.
        SQL IDENTYCZNE jak wcześniej!
        """
        cur.execute(f"""
            INSERT INTO {SCHEMA}.registrations 
            (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id))
    
    def create_two_disciplines_transaction(self, athlete_code: str, event_id: int,
                                          kata_discipline_id: int, category_kata_id: int,
                                          kumite_discipline_id: int, category_kumite_id: int) -> None:
        """
        Tworzy dwie rejestracje (Kata i Kumite) w ramach transakcji.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                cur.execute(f"""
                    INSERT INTO {SCHEMA}.registrations 
                    (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (athlete_code, event_id, kata_discipline_id, category_kata_id, None))
                
                cur.execute(f"""
                    INSERT INTO {SCHEMA}.registrations 
                    (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (athlete_code, event_id, kumite_discipline_id, None, category_kumite_id))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def update(self, registration_id: int, discipline_id: Optional[int], 
               category_kata_id: Optional[int], category_kumite_id: Optional[int]) -> None:
        """Aktualizuje rejestrację."""
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                cur.execute(f"""
                    UPDATE {SCHEMA}.registrations
                    SET discipline_id = %s, category_kata_id = %s, category_kumite_id = %s
                    WHERE id = %s
                """, (discipline_id, category_kata_id, category_kumite_id, registration_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def update_discipline(self, registration_id: int, discipline_type: str) -> None:
        """Aktualizuje pojedynczą dyscyplinę w rejestracji (ustawia NULL)."""
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                if discipline_type == "kata":
                    cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kata_id = NULL WHERE id = %s", (registration_id,))
                else:  # kumite
                    cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kumite_id = NULL WHERE id = %s", (registration_id,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def delete(self, registration_id: int, athlete_code: Optional[str] = None) -> None:
        """Usuwa rejestrację."""
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                if athlete_code:
                    cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
                else:
                    cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (registration_id,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def find_by_athlete_code_view(self, athlete_code: str) -> List[Tuple]:
        """
        Pobiera rejestracje zawodnika z widoku v_user_registrations.
        SQL IDENTYCZNE jak wcześniej!
        Zwraca listę krotek: (id, event_id, category_kata_id, category_kumite_id, event_name, start_date, end_date, kata_name, kumite_name)
        """
        with get_conn() as conn, conn.cursor() as cur:
            sql = f"""
                SELECT id, event_id, category_kata_id, category_kumite_id,
                       event_name, start_date, end_date,
                       kata_name, kumite_name
                FROM {SCHEMA}.v_user_registrations
                WHERE athlete_code = %s
                ORDER BY start_date, event_name
            """
            cur.execute(sql, (athlete_code,))
            return cur.fetchall()
    
    def update_discipline_transaction(self, reg_id: int, discipline_type: str, 
                                     kata_id: Optional[int], kumite_id: Optional[int]) -> str:
        """
        Aktualizuje pojedynczą dyscyplinę w rejestracji (transakcja).
        SQL IDENTYCZNE jak wcześniej!
        Zwraca komunikat o wyniku operacji.
        """
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                if discipline_type == "kata":
                    if not kata_id:
                        conn.rollback()
                        raise ValueError("Nie jesteś zapisany do Kata w tym zgłoszeniu.")
                    if not kumite_id:
                        # Usuń całą rejestrację
                        cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (reg_id,))
                        message = "Twoje zgłoszenie zostało wycofane (była to jedyna dyscyplina)."
                    else:
                        # Ustaw category_kata_id na NULL
                        cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kata_id = NULL WHERE id = %s", (reg_id,))
                        message = "Zostałeś wycofany z Kata."
                else:  # kumite
                    if not kumite_id:
                        conn.rollback()
                        raise ValueError("Nie jesteś zapisany do Kumite w tym zgłoszeniu.")
                    if not kata_id:
                        # Usuń całą rejestrację
                        cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (reg_id,))
                        message = "Twoje zgłoszenie zostało wycofane (była to jedyna dyscyplina)."
                    else:
                        # Ustaw category_kumite_id na NULL
                        cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kumite_id = NULL WHERE id = %s", (reg_id,))
                        message = "Zostałeś wycofany z Kumite."
                
                conn.commit()
                return message
            except Exception as e:
                conn.rollback()
                raise

