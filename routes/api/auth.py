from flask import Blueprint, request, jsonify, session
from datetime import date
import psycopg.errors
from database import get_conn
from config import SCHEMA

api_auth_bp = Blueprint('api_auth', __name__)


def get_clubs():
    """Pobiera listę klubów z bazy danych"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT name, city FROM {SCHEMA}.clubs ORDER BY name")
            return [{"name": r[0], "city": r[1]} for r in cur.fetchall()]
    except Exception:
        return []


# GET /api/clubs - pobierz listę klubów (do formularza rejestracji)
@api_auth_bp.get("/api/clubs")
def get_clubs_endpoint():
    """Zwraca listę klubów do formularza rejestracji"""
    clubs = get_clubs()
    return jsonify({"clubs": clubs})


# POST /api/register - rejestracja
@api_auth_bp.post("/api/register")
def register():
    data = request.get_json()
    
    login = (data.get("login") or "").strip()
    password = (data.get("password") or "").strip()
    country = (data.get("country_code") or "").strip().upper()
    nationality = (data.get("nationality") or "").strip()
    club_name = (data.get("club_name") or "").strip()
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    sex = (data.get("sex") or "").strip().upper()
    birth_raw = (data.get("birth_date") or "").strip()
    weight_raw = (data.get("weight") or "").strip()

    errors = []
    if not login:
        errors.append("Podaj login.")
    if not password:
        errors.append("Podaj hasło.")
    if len(country) != 3:
        errors.append("Kod kraju musi mieć 3 litery (np. POL).")
    if not nationality:
        errors.append("Podaj narodowość.")
    if not club_name:
        errors.append("Wybierz klub.")
    if sex not in ("M", "F"):
        errors.append("Płeć musi być M lub F.")

    # data urodzenia
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

    # waga
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

    insert_sql = f"""
        INSERT INTO {SCHEMA}.users
        (login, password, country_code, nationality, club_name, first_name, last_name, sex, birth_date, weight)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(insert_sql, (login, password, country, nationality, club_name, first, last, sex, birth_date, weight))
            user_id = cur.fetchone()[0]
        session.clear()
        session["user_id"] = user_id
        session["login"] = login
        return jsonify({"success": True, "message": "Konto utworzone.", "user_id": user_id}), 201
    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "Taki login już istnieje."}), 409
    except Exception as e:
        return jsonify({"error": f"Błąd podczas rejestracji: {e}"}), 500


# POST /api/login - logowanie
@api_auth_bp.post("/api/login")
def login():
    data = request.get_json()
    
    login_val = (data.get("login") or "").strip()
    password_val = (data.get("password") or "").strip()

    if not login_val:
        return jsonify({"error": "Podaj login."}), 400
    if not password_val:
        return jsonify({"error": "Podaj hasło."}), 400

    sql = f"SELECT id, is_admin FROM {SCHEMA}.users WHERE login=%s AND password=%s"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (login_val, password_val))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Błędny login lub hasło."}), 401

    session.clear()
    session["user_id"] = row[0]
    session["login"] = login_val
    session["is_admin"] = row[1] if row[1] else False
    return jsonify({
        "success": True,
        "message": "Zalogowano.",
        "user_id": row[0],
        "is_admin": session["is_admin"]
    })


# POST /api/logout - wylogowanie
@api_auth_bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Wylogowano."})


# GET /api/auth/check - sprawdź czy użytkownik jest zalogowany
@api_auth_bp.get("/api/auth/check")
def check_auth():
    """Sprawdza czy użytkownik jest zalogowany i zwraca podstawowe info o sesji"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200
    
    return jsonify({
        "authenticated": True,
        "user_id": user_id,
        "login": session.get("login"),
        "is_admin": session.get("is_admin", False)
    })

