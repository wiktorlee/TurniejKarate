from flask import Blueprint, request, jsonify, session
from datetime import date
import psycopg.errors
from database import get_conn
from config import SCHEMA
from utils import get_system_status

api_categories_bp = Blueprint('api_categories', __name__)


# GET /api/categories - pobierz listę eventów, dyscyplin i kategorii
@api_categories_bp.get("/api/categories")
def get_categories():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany, aby zobaczyć kategorie."}), 401

    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Sprawdź status systemu
            system_status = get_system_status()
            if system_status != 'ACTIVE':
                return jsonify({
                    "error": "System jest w stanie zakończonym. Zapisy są zablokowane.",
                    "system_status": system_status
                }), 403
            
            # Pobierz dane użytkownika
            cur.execute(f"SELECT athlete_code, sex, birth_date, weight FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                return jsonify({"error": "Nie masz przypisanego kodu zawodnika."}), 400
            athlete_code, user_sex, birth_date, weight = row[0], row[1], row[2], row[3]

            # Pobierz eventy
            cur.execute(f"SELECT id, name FROM {SCHEMA}.events WHERE is_active = true ORDER BY start_date, name")
            events = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # Pobierz dyscypliny
            cur.execute(f"SELECT id, name FROM {SCHEMA}.disciplines ORDER BY name")
            disciplines = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # Pobierz kategorie Kata
            cur.execute(f"""
                SELECT id, name FROM {SCHEMA}.categories_kata 
                WHERE is_active = true AND sex = %s
                ORDER BY name
            """, (user_sex,))
            categories_kata = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # Pobierz kategorie Kumite
            cur.execute(f"""
                SELECT id, name FROM {SCHEMA}.categories_kumite 
                WHERE is_active = true AND sex = %s
                ORDER BY name
            """, (user_sex,))
            categories_kumite = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # Sprawdź czy ma rejestracje
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.registrations WHERE athlete_code=%s", (athlete_code,))
            registration_count = cur.fetchone()[0]
            has_registration = registration_count > 0

            return jsonify({
                "events": events,
                "disciplines": disciplines,
                "categories_kata": categories_kata,
                "categories_kumite": categories_kumite,
                "has_registration": has_registration
            })
    except Exception as e:
        return jsonify({"error": f"Wystąpił błąd bazy danych: {e}"}), 500


# POST /api/categories/register - rejestracja na kategorię
@api_categories_bp.post("/api/categories/register")
def register_to_category():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany."}), 401

    data = request.get_json()
    event_id = data.get("event_id")
    discipline_kata = data.get("discipline_kata", False)
    discipline_kumite = data.get("discipline_kumite", False)
    category_kata_id = data.get("category_kata_id")
    category_kumite_id = data.get("category_kumite_id")

    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Sprawdź status systemu
            system_status = get_system_status()
            if system_status != 'ACTIVE':
                return jsonify({"error": "System jest w stanie zakończonym. Zapisy są zablokowane."}), 403

            # Walidacja
            if not event_id:
                return jsonify({"error": "Nie wybrano eventu."}), 400
            if not discipline_kata and not discipline_kumite:
                return jsonify({"error": "Wybierz przynajmniej jedną dyscyplinę (Kata lub Kumite)."}), 400
            if discipline_kata and not category_kata_id:
                return jsonify({"error": "Wybierz kategorię dla Kata."}), 400
            if discipline_kumite and not category_kumite_id:
                return jsonify({"error": "Wybierz kategorię dla Kumite."}), 400

            # Pobierz dane użytkownika
            cur.execute(f"SELECT athlete_code, sex, birth_date, weight FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                return jsonify({"error": "Nie masz przypisanego kodu zawodnika."}), 400
            athlete_code, user_sex, birth_date, weight = row[0], row[1], row[2], row[3]

            # Walidacja wieku i wagi
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

            # Walidacja Kata
            if discipline_kata:
                cur.execute(f"""
                    SELECT name, sex, min_age, max_age
                    FROM {SCHEMA}.categories_kata
                    WHERE id = %s AND is_active = true
                """, (category_kata_id,))
                kata_cat = cur.fetchone()
                if not kata_cat:
                    return jsonify({"error": "Nie znaleziono kategorii Kata."}), 404
                kata_name, kata_sex, kata_min_age, kata_max_age = kata_cat

                if user_sex != kata_sex:
                    return jsonify({"error": f"Nie możesz zapisać się do kategorii Kata {kata_name} (inna płeć)."}), 400
                if kata_min_age and age < kata_min_age:
                    return jsonify({"error": f"Za młody do kategorii Kata {kata_name} ({age} lat, wymagane min {kata_min_age})."}), 400
                if kata_max_age and age > kata_max_age:
                    return jsonify({"error": f"Za stary do kategorii Kata {kata_name} ({age} lat, dopuszczalne max {kata_max_age})."}), 400

            # Walidacja Kumite
            if discipline_kumite:
                cur.execute(f"""
                    SELECT name, sex, min_age, max_age, min_weight, max_weight
                    FROM {SCHEMA}.categories_kumite
                    WHERE id = %s AND is_active = true
                """, (category_kumite_id,))
                kumite_cat = cur.fetchone()
                if not kumite_cat:
                    return jsonify({"error": "Nie znaleziono kategorii Kumite."}), 404
                kumite_name, kumite_sex, kumite_min_age, kumite_max_age, kumite_min_weight, kumite_max_weight = kumite_cat

                if user_sex != kumite_sex:
                    return jsonify({"error": f"Nie możesz zapisać się do kategorii Kumite {kumite_name} (inna płeć)."}), 400
                if kumite_min_age and age < kumite_min_age:
                    return jsonify({"error": f"Za młody do kategorii Kumite {kumite_name} ({age} lat, wymagane min {kumite_min_age})."}), 400
                if kumite_max_age and age > kumite_max_age:
                    return jsonify({"error": f"Za stary do kategorii Kumite {kumite_name} ({age} lat, dopuszczalne max {kumite_max_age})."}), 400
                if kumite_min_weight and weight and weight < kumite_min_weight:
                    return jsonify({"error": f"Za lekki na kategorię Kumite {kumite_name} (min {kumite_min_weight} kg)."}), 400
                if kumite_max_weight and weight and weight > kumite_max_weight:
                    return jsonify({"error": f"Za ciężki na kategorię Kumite {kumite_name} (max {kumite_max_weight} kg)."}), 400

            # Sprawdź istniejącą rejestrację
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE athlete_code=%s AND event_id=%s", (athlete_code, event_id))
            existing = cur.fetchone()

            # Pobranie discipline_id
            discipline_id = None
            if discipline_kata and not discipline_kumite:
                cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kata' LIMIT 1")
                disc_row = cur.fetchone()
                if disc_row:
                    discipline_id = disc_row[0]
            elif discipline_kumite and not discipline_kata:
                cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kumite' LIMIT 1")
                disc_row = cur.fetchone()
                if disc_row:
                    discipline_id = disc_row[0]

            if existing:
                # Aktualizacja istniejącego zgłoszenia
                reg_id = existing[0]
                cur.execute(f"""
                    UPDATE {SCHEMA}.registrations
                    SET discipline_id = %s, category_kata_id = %s, category_kumite_id = %s
                    WHERE id = %s
                """, (discipline_id, category_kata_id if discipline_kata else None, 
                      category_kumite_id if discipline_kumite else None, reg_id))
                conn.commit()
                return jsonify({"success": True, "message": "Zgłoszenie na ten event zostało zaktualizowane!"})
            else:
                # Nowa rejestracja
                if discipline_kata and discipline_kumite:
                    # Dwie osobne rejestracje
                    try:
                        conn.execute("BEGIN")
                        
                        cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kata' LIMIT 1")
                        kata_disc_row = cur.fetchone()
                        kata_discipline_id = kata_disc_row[0] if kata_disc_row else None
                        
                        cur.execute(f"""
                            INSERT INTO {SCHEMA}.registrations 
                            (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (athlete_code, event_id, kata_discipline_id, category_kata_id, None))
                        
                        cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kumite' LIMIT 1")
                        kumite_disc_row = cur.fetchone()
                        kumite_discipline_id = kumite_disc_row[0] if kumite_disc_row else None
                        
                        cur.execute(f"""
                            INSERT INTO {SCHEMA}.registrations 
                            (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (athlete_code, event_id, kumite_discipline_id, None, category_kumite_id))
                        
                        conn.commit()
                        return jsonify({"success": True, "message": "Zostałeś pomyślnie zapisany na zawody w obu dyscyplinach!"})
                    except Exception as e:
                        conn.rollback()
                        return jsonify({"error": f"Błąd podczas rejestracji na obie dyscypliny: {e}"}), 500
                else:
                    # Pojedyncza rejestracja
                    cur.execute(f"""
                        INSERT INTO {SCHEMA}.registrations 
                        (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (athlete_code, event_id, discipline_id, 
                          category_kata_id if discipline_kata else None,
                          category_kumite_id if discipline_kumite else None))
                    conn.commit()
                    return jsonify({"success": True, "message": "Zostałeś pomyślnie zapisany na zawody!"})

    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "Jesteś już zapisany (UniqueViolation)."}), 409
    except Exception as e:
        return jsonify({"error": f"Wystąpił błąd bazy danych: {e}"}), 500

