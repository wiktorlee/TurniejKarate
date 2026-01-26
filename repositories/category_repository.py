from database import get_conn
from config import SCHEMA
from typing import List, Dict, Optional, Tuple

class CategoryRepository:
    """Repozytorium dla kategorii"""
    
    def find_kata_by_sex(self, sex: str) -> List[Dict]:
        """Znajduje kategorie Kata dla danej płci."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, name FROM {SCHEMA}.categories_kata 
                WHERE is_active = true AND sex = %s
                ORDER BY name
            """, (sex,))
            return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    
    def find_kumite_by_sex(self, sex: str) -> List[Dict]:
        """Znajduje kategorie Kumite dla danej płci."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, name FROM {SCHEMA}.categories_kumite 
                WHERE is_active = true AND sex = %s
                ORDER BY name
            """, (sex,))
            return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    
    def find_kata_by_id(self, category_id: int) -> Optional[Tuple]:
        """Znajduje kategorię Kata po ID. Zwraca: (name, sex, min_age, max_age)"""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT name, sex, min_age, max_age
                FROM {SCHEMA}.categories_kata
                WHERE id = %s AND is_active = true
            """, (category_id,))
            return cur.fetchone()
    
    def find_kumite_by_id(self, category_id: int) -> Optional[Tuple]:
        """Znajduje kategorię Kumite po ID. Zwraca: (name, sex, min_age, max_age, min_weight, max_weight)"""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT name, sex, min_age, max_age, min_weight, max_weight
                FROM {SCHEMA}.categories_kumite
                WHERE id = %s AND is_active = true
            """, (category_id,))
            return cur.fetchone()
    
    def get_kata_name(self, category_id: int) -> Optional[str]:
        """Pobiera nazwę kategorii Kata."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT name FROM {SCHEMA}.categories_kata WHERE id = %s
            """, (category_id,))
            row = cur.fetchone()
            return row[0] if row else None
    
    def get_kumite_name(self, category_id: int) -> Optional[str]:
        """Pobiera nazwę kategorii Kumite."""
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT name FROM {SCHEMA}.categories_kumite WHERE id = %s
            """, (category_id,))
            row = cur.fetchone()
            return row[0] if row else None


