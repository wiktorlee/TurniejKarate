from database import get_conn
from config import SCHEMA
from typing import Dict, List, Tuple, Optional

class AdminRepository:
    """
    Repozytorium dla operacji admina.
    Wszystkie zapytania SQL IDENTYCZNE jak wcześniej!
    Procedury SQL z Supabase - BEZ ZMIAN!
    """
    
    def get_system_status(self) -> Dict:
        """
        Pobiera status systemu.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT status, simulation_date, reset_date, updated_at
                FROM {SCHEMA}.system_status 
                ORDER BY id DESC LIMIT 1
            """)
            row = cur.fetchone()
            return {
                "status": row[0] if row else "ACTIVE",
                "simulation_date": row[1] if row and row[1] else None,
                "reset_date": row[2] if row and row[2] else None,
                "updated_at": row[3] if row and row[3] else None
            }
    
    def get_statistics(self) -> Dict:
        """
        Pobiera statystyki systemu.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.users WHERE is_dummy = true")
            dummy_count = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.events WHERE is_active = true")
            active_events = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.results")
            results_count = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.registrations")
            registrations_count = cur.fetchone()[0]
            
            return {
                "dummy_count": dummy_count,
                "active_events": active_events,
                "results_count": results_count,
                "registrations_count": registrations_count
            }
    
    def call_simulate_competitions(self) -> List[Tuple]:
        """
        Wywołuje procedurę simulate_competitions() z Supabase.
        
        PROCEDURA W SUPABASE - BEZ ZMIAN!
        Wywołanie IDENTYCZNE jak wcześniej!
        
        Zwraca: Lista krotek (message, events_processed, results_created)
        """
        with get_conn() as conn, conn.cursor() as cur:
            # IDENTYCZNE wywołanie procedury z Supabase!
            cur.execute(f"SELECT * FROM {SCHEMA}.simulate_competitions()")
            return cur.fetchall()
    
    def call_restore_dummy_athletes(self) -> List[Tuple]:
        """
        Wywołuje procedurę restore_dummy_athletes_registrations() z Supabase.
        
        PROCEDURA W SUPABASE - BEZ ZMIAN!
        Wywołanie IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            # IDENTYCZNE wywołanie procedury z Supabase!
            cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
            return cur.fetchall()
    
    def reset_system(self, restore_dummies: bool) -> Dict:
        """
        Resetuje system.
        SQL IDENTYCZNE jak wcześniej!
        """
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            
            cur.execute(f"DELETE FROM {SCHEMA}.results")
            deleted_results = cur.rowcount
            
            cur.execute(f"DELETE FROM {SCHEMA}.draw_fight")
            deleted_fights = cur.rowcount
            
            restored_count = 0
            if restore_dummies:
                cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
                results = cur.fetchall()
                restored_count = sum(row[2] for row in results if isinstance(row[2], int)) if results else 0
            
            cur.execute(f"""
                UPDATE {SCHEMA}.system_status 
                SET status = 'ACTIVE', reset_date = now(), updated_at = now()
                WHERE id = (SELECT id FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1)
            """)
            
            conn.commit()
            
            return {
                "deleted_results": deleted_results,
                "deleted_fights": deleted_fights,
                "restored_count": restored_count
            }
    
    def update_system_status(self, status: str) -> None:
        """Aktualizuje status systemu."""
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            try:
                cur.execute(f"""
                    UPDATE {SCHEMA}.system_status 
                    SET status = %s, simulation_date = now(), updated_at = now()
                    WHERE id = (SELECT id FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1)
                """, (status,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise


