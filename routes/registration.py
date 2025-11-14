from flask import Blueprint, render_template, redirect, url_for, session, flash
from database import get_conn
from config import SCHEMA

registration_bp = Blueprint('registration', __name__)


#Moje zgłoszenie
@registration_bp.get("/my-registration")
def my_registration():
    uid = session.get("user_id")
    if not uid:
        flash("Musisz być zalogowany, aby zobaczyć swoje zgłoszenie.", "error")
        return redirect(url_for("auth.login"))

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Nie masz przypisanego kodu zawodnika.", "error")
                return redirect(url_for("profile.profile"))
            athlete_code = row[0]

            sql = f"""
                SELECT r.id, c.name
                FROM {SCHEMA}.registrations r
                JOIN {SCHEMA}.categories c ON r.category_id = c.id
                WHERE r.athlete_code = %s
            """
            cur.execute(sql, (athlete_code,))
            row = cur.fetchone()

            reg_data = None
            if row:
                reg_data = {"reg_id": row[0], "category_name": row[1]}

            return render_template("my_registration.html", registration=reg_data)
    except Exception as e:
        flash(f"Błąd podczas pobierania zgłoszenia: {e}", "error")
        return redirect(url_for("profile.profile"))


#Wycofanie zgłoszenia
@registration_bp.post("/withdraw")
def withdraw():
    uid = session.get("user_id")
    if not uid:
        flash("Brak sesji.", "error")
        return redirect(url_for("auth.login"))

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Nie masz przypisanego kodu zawodnika.", "error")
                return redirect(url_for("profile.profile"))
            athlete_code = row[0]

            cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE athlete_code = %s", (athlete_code,))
            conn.commit()
            flash("Twoje zgłoszenie zostało wycofane.", "success")
            return redirect(url_for("categories.categories"))

    except Exception as e:
        flash(f"Błąd podczas wycofywania zgłoszenia: {e}", "error")
        return redirect(url_for("registration.my_registration"))

