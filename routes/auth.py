from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from datetime import date
import psycopg.errors
from database import get_conn
from config import SCHEMA

auth_bp = Blueprint('auth', __name__)


def get_clubs():
    """Pobiera listę klubów z bazy danych"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT name, city FROM {SCHEMA}.clubs ORDER BY name")
            return [{"name": r[0], "city": r[1]} for r in cur.fetchall()]
    except Exception:
        return []


#Rejestracja
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # POST handling moved to API - this route only serves template
    return render_template("register.html")


#Logowanie
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # POST handling moved to API - this route only serves template
    return render_template("login.html")


#Wylogowanie
@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("auth.login"))

