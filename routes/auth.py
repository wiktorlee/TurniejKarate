from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from datetime import date
import psycopg.errors
from database import get_conn
from config import SCHEMA

auth_bp = Blueprint('auth', __name__)


#Rejestracja
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    login = (request.form.get("login") or "").strip()
    password = (request.form.get("password") or "").strip()
    country = (request.form.get("country_code") or "").strip().upper()
    first = (request.form.get("first_name") or "").strip()
    last = (request.form.get("last_name") or "").strip()
    sex = (request.form.get("sex") or "").strip().upper()
    birth_raw = (request.form.get("birth_date") or "").strip()
    weight_raw = (request.form.get("weight") or "").strip()

    errors = []
    if not login:
        errors.append("Podaj login.")
    if not password:
        errors.append("Podaj hasło.")
    if len(country) != 3:
        errors.append("Kod kraju musi mieć 3 litery (np. POL).")
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

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("register.html", form=request.form), 400

    insert_sql = f"""
        INSERT INTO {SCHEMA}.users
        (login, password, country_code, first_name, last_name, sex, birth_date, weight)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(insert_sql, (login, password, country, first, last, sex, birth_date, weight))
            user_id = cur.fetchone()[0]
        session.clear()
        session["user_id"] = user_id
        session["login"] = login
        flash("Konto utworzone.", "success")
        return redirect(url_for("profile.profile"))
    except psycopg.errors.UniqueViolation:
        flash("Taki login już istnieje.", "error")
        return render_template("register.html", form=request.form), 409
    except Exception as e:
        flash(f"Błąd podczas rejestracji: {e}", "error")
        return render_template("register.html", form=request.form), 500


#Logowanie
@auth_bp.route("/login", methods=["GET", "POST"])
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
    return redirect(url_for("profile.profile"))


#Wylogowanie
@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("auth.login"))

