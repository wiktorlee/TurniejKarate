from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from datetime import date
from database import get_conn
from config import SCHEMA

profile_bp = Blueprint('profile', __name__)


def get_clubs():
    """Pobiera listę klubów z bazy danych"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT name, city FROM {SCHEMA}.clubs ORDER BY name")
            return [{"name": r[0], "city": r[1]} for r in cur.fetchall()]
    except Exception:
        return []


#Profil
@profile_bp.get("/profile")
def profile():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    # Data loading moved to API/JS - this route only serves template
    return render_template("profile.html")


#Edycja profilu
@profile_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    # Data loading and POST handling moved to API/JS - this route only serves template
    return render_template("edit_profile.html")

