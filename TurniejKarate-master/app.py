import os
from datetime import date
from dotenv import load_dotenv
from flask import (
    Flask, jsonify, request, render_template, redirect, url_for, session, flash
)
import psycopg

# --- konfiguracja ---
load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
DB_URL = os.getenv("DATABASE_URL")
SCHEMA = "karate"

def get_conn():
    if not DB_URL:
        raise RuntimeError("Brak DATABASE_URL w .env")
    return psycopg.connect(DB_URL, connect_timeout=5)

# landing – pokaż UI
@app.get("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return redirect(url_for("register"))

@app.get("/health/db")
def health_db():
    if not DB_URL:
        return jsonify(ok=False, error="Brak DATABASE_URL w .env"), 500
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
        return jsonify(ok=True, db_version=version)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

# ---------- REJESTRACJA ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    login = (request.form.get("login") or "").strip()
    password = (request.form.get("password") or "").strip()
    country = (request.form.get("country_code") or "").strip().upper()
    first = (request.form.get("first_name") or "").strip()
    last  = (request.form.get("last_name") or "").strip()
    sex   = (request.form.get("sex") or "").strip().upper()
    birth_raw = (request.form.get("birth_date") or "").strip()

    errors = []
    if not login:
        errors.append("Podaj login.")
    if not password:
        errors.append("Podaj hasło.")
    if len(country) != 3:
        errors.append("Kod kraju musi mieć 3 litery (np. POL).")
    if sex not in ("M", "F"):
        errors.append("Płeć musi być M lub F.")

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

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("register.html", form=request.form), 400

    insert_sql = f"""
        INSERT INTO {SCHEMA}.users
        (login, password, country_code, first_name, last_name, sex, birth_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(insert_sql, (login, password, country, first, last, sex, birth_date))
            user_id = cur.fetchone()[0]
        session.clear()
        session["user_id"] = user_id
        session["login"] = login
        flash("Konto utworzone.", "success")
        return redirect(url_for("profile"))
    except psycopg.errors.UniqueViolation:
        flash("Taki login już istnieje.", "error")
        return render_template("register.html", form=request.form), 409
    except Exception as e:
        flash(f"Błąd podczas rejestracji: {e}", "error")
        return render_template("register.html", form=request.form), 500

# ---------- LOGOWANIE ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    login_val = (request.form.get("login") or "").strip()
    password_val = (request.form.get("password") or "").strip()

    if not login_val:
        flash("Podaj login.", "error")
        return render_template("login.html"), 400
    if not password_val:
        flash("Podaj hasło.", "error")
        return render_template("login.html"), 400

    sql = f"SELECT id FROM {SCHEMA}.users WHERE login=%s AND password=%s"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (login_val, password_val))
        row = cur.fetchone()
        if not row:
            flash("Błędny login lub hasło.", "error")
            return render_template("login.html"), 401

    session.clear()
    session["user_id"] = row[0]
    session["login"] = login_val
    flash("Zalogowano.", "success")
    return redirect(url_for("profile"))

# ---------- PROFIL ----------
@app.get("/profile")
def profile():
    uid = session.get("user_id")
    if not uid:
        flash("Brak sesji – zaloguj się albo zarejestruj.", "error")
        return redirect(url_for("login"))

    sql = f"""
        SELECT id, login, country_code, first_name, last_name, sex, birth_date, athlete_code
        FROM {SCHEMA}.users
        WHERE id=%s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (uid,))
        row = cur.fetchone()

    if not row:
        flash("Użytkownik nie istnieje.", "error")
        return redirect(url_for("login"))

    user = {
        "id": row[0],
        "login": row[1],
        "country_code": row[2],
        "first_name": row[3],
        "last_name": row[4],
        "sex": row[5],
        "birth_date": row[6],
        "athlete_code": row[7],
    }
    return render_template("profile.html", user=user)

# ---------- WYLOGOWANIE ----------
@app.get("/logout")
def logout():
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)


    # ---------- KATEGORIE I ZAPISY (ETAP 2) ----------
    @app.route("/categories", methods=["GET", "POST"])
    def categories():
        uid = session.get("user_id")
        if not uid:
            flash("Musisz być zalogowany, aby zobaczyć kategorie.", "error")
            return redirect(url_for("login"))

        try:
            with get_conn() as conn, conn.cursor() as cur:
                # 1. Sprawdź, czy użytkownik jest już zapisany
                check_sql = f"SELECT id FROM {SCHEMA}.registrations WHERE user_id=%s"
                cur.execute(check_sql, (uid,))
                existing_registration = cur.fetchone()

                if existing_registration:
                    flash("Jesteś już zapisany do kategorii. Możesz wycofać swoje zgłoszenie w 'Moje zgłoszenie'.",
                          "info")
                    return redirect(url_for("my_registration"))

                # 2. Obsługa zapisu (POST)
                if request.method == "POST":
                    category_id = request.form.get("category_id")
                    if not category_id:
                        flash("Nie wybrano kategorii.", "error")
                        return redirect(url_for("categories"))

                    # Zapisujemy używając user_id z sesji
                    insert_sql = f"INSERT INTO {SCHEMA}.registrations (user_id, category_id) VALUES (%s, %s)"
                    cur.execute(insert_sql, (uid, category_id))
                    conn.commit()

                    flash("Zostałeś pomyślnie zapisany na zawody!", "success")
                    return redirect(url_for("my_registration"))

                # 3. Wyświetlanie formularza (GET)
                # Pobieramy ID i nazwę kategorii z bazy
                cur.execute(f"SELECT id, name FROM {SCHEMA}.categories ORDER BY name")
                all_categories_raw = cur.fetchall()
                # Konwertujemy na listę słowników dla szablonu HTML
                all_categories = [{"id": row[0], "name": row[1]} for row in all_categories_raw]

                return render_template("categories.html", categories=all_categories)

        except psycopg.errors.UniqueViolation:
            # To zabezpieczenie na wypadek, gdyby użytkownik próbował się zapisać
            # (np. w drugiej zakładce), mimo że już jest zapisany.
            flash("Błąd: Jesteś już zapisany (UniqueViolation).", "error")
            return redirect(url_for("my_registration"))
        except Exception as e:
            flash(f"Wystąpił błąd bazy danych: {e}", "error")
            return redirect(url_for("profile"))


    @app.get("/my-registration")
    def my_registration():
        uid = session.get("user_id")
        if not uid:
            flash("Musisz być zalogowany, aby zobaczyć swoje zgłoszenie.", "error")
            return redirect(url_for("login"))

        # Pobieramy nazwę kategorii, do której zapisany jest użytkownik
        sql = f"""
            SELECT r.id, c.name
            FROM {SCHEMA}.registrations r
            JOIN {SCHEMA}.categories c ON r.category_id = c.id
            WHERE r.user_id = %s
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (uid,))
            row = cur.fetchone()

        reg_data = None
        if row:
            reg_data = {"reg_id": row[0], "category_name": row[1]}

        return render_template("my_registration.html", registration=reg_data)


    @app.post("/withdraw")
    def withdraw():
        uid = session.get("user_id")
        if not uid:
            flash("Brak sesji.", "error")
            return redirect(url_for("login"))

        # Usuwamy zgłoszenie na podstawie user_id
        sql = f"DELETE FROM {SCHEMA}.registrations WHERE user_id = %s"
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(sql, (uid,))
                conn.commit()
            flash("Twoje zgłoszenie zostało wycofane.", "success")
            return redirect(url_for("categories"))  # Przekieruj z powrotem do zapisów
        except Exception as e:
            flash(f"Błąd podczas wycofywania zgłoszenia: {e}", "error")
            return redirect(url_for("my_registration"))
