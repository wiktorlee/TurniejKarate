from flask import Blueprint, render_template, redirect, url_for, session, flash
from database import get_conn
from config import SCHEMA

profile_bp = Blueprint('profile', __name__)


#Profil
@profile_bp.get("/profile")
def profile():
    uid = session.get("user_id")
    if not uid:
        flash("Brak sesji – zaloguj się albo zarejestruj.", "error")
        return redirect(url_for("auth.login"))

    sql = f"""
        SELECT id, login, country_code, first_name, last_name, sex, birth_date, weight, athlete_code
        FROM {SCHEMA}.users
        WHERE id=%s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (uid,))
        row = cur.fetchone()

    if not row:
        flash("Użytkownik nie istnieje.", "error")
        return redirect(url_for("auth.login"))

    user = {
        "id": row[0],
        "login": row[1],
        "country_code": row[2],
        "first_name": row[3],
        "last_name": row[4],
        "sex": row[5],
        "birth_date": row[6],
        "weight": row[7],
        "athlete_code": row[8],
    }
    return render_template("profile.html", user=user)

