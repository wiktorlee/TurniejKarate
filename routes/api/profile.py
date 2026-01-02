from flask import Blueprint, request, jsonify, session
from datetime import date
from database import get_conn
from config import SCHEMA

api_profile_bp = Blueprint('api_profile', __name__)


def get_clubs():
    """Pobiera listę klubów z bazy danych"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT name, city FROM {SCHEMA}.clubs ORDER BY name")
            return [{"name": r[0], "city": r[1]} for r in cur.fetchall()]
    except Exception:
        return []


# GET /api/profile - pobierz profil użytkownika
@api_profile_bp.get("/api/profile")
def get_profile():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji – zaloguj się albo zarejestruj."}), 401

    sql = f"""
        SELECT id, login, country_code, nationality, club_name, first_name, last_name, sex, birth_date, weight, athlete_code
        FROM {SCHEMA}.users
        WHERE id=%s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (uid,))
        row = cur.fetchone()

    if not row:
        return jsonify({"error": "Użytkownik nie istnieje."}), 404

    user = {
        "id": row[0],
        "login": row[1],
        "country_code": row[2],
        "nationality": row[3],
        "club_name": row[4],
        "first_name": row[5],
        "last_name": row[6],
        "sex": row[7],
        "birth_date": row[8].isoformat() if row[8] else None,
        "weight": float(row[9]) if row[9] else None,
        "athlete_code": row[10],
    }
    clubs = get_clubs()
    return jsonify({"user": user, "clubs": clubs})


# PUT /api/profile - aktualizuj profil użytkownika
@api_profile_bp.put("/api/profile")
def update_profile():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji – zaloguj się albo zarejestruj."}), 401

    data = request.get_json()
    
    country = (data.get("country_code") or "").strip().upper()
    nationality = (data.get("nationality") or "").strip()
    club_name = (data.get("club_name") or "").strip()
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    sex = (data.get("sex") or "").strip().upper()
    birth_raw = (data.get("birth_date") or "").strip()
    weight_raw = (data.get("weight") or "").strip()
    password = (data.get("password") or "").strip()

    errors = []
    
    if len(country) != 3:
        errors.append("Kod kraju musi mieć 3 litery (np. POL).")
    if not nationality:
        errors.append("Podaj narodowość.")
    if not club_name:
        errors.append("Wybierz klub.")
    if sex not in ("M", "F"):
        errors.append("Płeć musi być M lub F.")

    # Walidacja daty urodzenia
    birth_date = None
    if birth_raw:
        try:
            y, m, d = map(int, birth_raw.split("-"))
            birth_date = date(y, m, d)
            if birth_date > date.today():
                errors.append("Data urodzenia nie może być w przyszłości.")
        except Exception:
            errors.append("Niepoprawny format daty (YYYY-MM-DD).")
    else:
        errors.append("Data urodzenia jest wymagana.")

    # Walidacja wagi
    weight = None
    if weight_raw:
        try:
            weight = float(weight_raw)
            if weight <= 0:
                errors.append("Waga musi być dodatnia.")
        except ValueError:
            errors.append("Niepoprawny format wagi.")
    else:
        errors.append("Podaj wagę.")

    # Weryfikacja istnienia klubu
    if club_name:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT name FROM {SCHEMA}.clubs WHERE name = %s", (club_name,))
            if not cur.fetchone():
                errors.append("Wybrany klub nie istnieje.")

    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    try:
        with get_conn() as conn, conn.cursor() as cur:
            if password:
                # Aktualizacja z hasłem
                update_sql = f"""
                    UPDATE {SCHEMA}.users
                    SET country_code = %s, nationality = %s, club_name = %s,
                        first_name = %s, last_name = %s, sex = %s,
                        birth_date = %s, weight = %s, password = %s
                    WHERE id = %s
                """
                cur.execute(update_sql, (country, nationality, club_name, first, last, sex, birth_date, weight, password, uid))
            else:
                # Aktualizacja bez hasła
                update_sql = f"""
                    UPDATE {SCHEMA}.users
                    SET country_code = %s, nationality = %s, club_name = %s,
                        first_name = %s, last_name = %s, sex = %s,
                        birth_date = %s, weight = %s
                    WHERE id = %s
                """
                cur.execute(update_sql, (country, nationality, club_name, first, last, sex, birth_date, weight, uid))
            conn.commit()
            return jsonify({"success": True, "message": "Profil został zaktualizowany!"})
    except Exception as e:
        return jsonify({"error": f"Błąd podczas aktualizacji profilu: {e}"}), 500

