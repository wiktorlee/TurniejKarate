import psycopg
from config import DB_URL


def get_conn():
    if not DB_URL:
        raise RuntimeError("Brak DATABASE_URL w .env")
    return psycopg.connect(DB_URL, connect_timeout=5)






























