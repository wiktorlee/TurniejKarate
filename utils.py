from database import get_conn
from config import SCHEMA

def get_system_status():
    """Pobiera aktualny status systemu z bazy danych"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT status FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            return row[0] if row else 'ACTIVE'
    except Exception:
        # W przypadku błędu zwróć ACTIVE jako domyślny status
        return 'ACTIVE'














