from flask import Blueprint, request, render_template, redirect, url_for, session, flash
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
                SELECT r.id, r.event_id, r.category_kata_id, r.category_kumite_id,
                       e.name as event_name, e.start_date, e.end_date,
                       ck.name as kata_name,
                       ckm.name as kumite_name
                FROM {SCHEMA}.registrations r
                LEFT JOIN {SCHEMA}.events e ON r.event_id = e.id
                LEFT JOIN {SCHEMA}.categories_kata ck ON r.category_kata_id = ck.id
                LEFT JOIN {SCHEMA}.categories_kumite ckm ON r.category_kumite_id = ckm.id
                WHERE r.athlete_code = %s
                ORDER BY e.start_date, e.name
            """
            cur.execute(sql, (athlete_code,))
            rows = cur.fetchall()

            registrations = []
            for row in rows:
                registrations.append({
                    "reg_id": row[0],
                    "event_id": row[1],
                    "category_kata_id": row[2],
                    "category_kumite_id": row[3],
                    "event_name": row[4],
                    "start_date": row[5],
                    "end_date": row[6],
                    "kata_name": row[7],
                    "kumite_name": row[8]
                })

            return render_template("my_registration.html", registrations=registrations)
    except Exception as e:
        flash(f"Błąd podczas pobierania zgłoszenia: {e}", "error")
        return redirect(url_for("profile.profile"))


#Wycofanie całego zgłoszenia (konkretnej rejestracji)
@registration_bp.post("/withdraw")
def withdraw():
    uid = session.get("user_id")
    if not uid:
        flash("Brak sesji.", "error")
        return redirect(url_for("auth.login"))

    registration_id = request.form.get("registration_id")
    if not registration_id:
        flash("Brak ID zgłoszenia.", "error")
        return redirect(url_for("registration.my_registration"))

    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Weryfikacja właściciela zgłoszenia
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Nie masz przypisanego kodu zawodnika.", "error")
                return redirect(url_for("profile.profile"))
            athlete_code = row[0]

            # Weryfikacja przynależności rejestracji
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            reg = cur.fetchone()
            if not reg:
                flash("Nie znaleziono zgłoszenia lub nie masz uprawnień do jego usunięcia.", "error")
                return redirect(url_for("registration.my_registration"))

            cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            conn.commit()
            flash("Twoje zgłoszenie zostało wycofane.", "success")
            return redirect(url_for("registration.my_registration"))

    except Exception as e:
        flash(f"Błąd podczas wycofywania zgłoszenia: {e}", "error")
        return redirect(url_for("registration.my_registration"))


#Wycofanie pojedynczej dyscypliny
@registration_bp.post("/withdraw-discipline")
def withdraw_discipline():
    uid = session.get("user_id")
    if not uid:
        flash("Brak sesji.", "error")
        return redirect(url_for("auth.login"))

    registration_id = request.form.get("registration_id")
    discipline_type = request.form.get("discipline_type")
    
    if not registration_id:
        flash("Brak ID zgłoszenia.", "error")
        return redirect(url_for("registration.my_registration"))
    
    if discipline_type not in ("kata", "kumite"):
        flash("Nieprawidłowy typ dyscypliny.", "error")
        return redirect(url_for("registration.my_registration"))

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Nie masz przypisanego kodu zawodnika.", "error")
                return redirect(url_for("profile.profile"))
            athlete_code = row[0]

            # Weryfikacja istnienia zgłoszenia
            cur.execute(f"SELECT id, category_kata_id, category_kumite_id FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            reg = cur.fetchone()
            if not reg:
                flash("Nie masz aktywnego zgłoszenia lub nie masz uprawnień.", "error")
                return redirect(url_for("registration.my_registration"))

            reg_id, kata_id, kumite_id = reg

            # Usuwanie wybranej dyscypliny
            if discipline_type == "kata":
                if not kata_id:
                    flash("Nie jesteś zapisany do Kata w tym zgłoszeniu.", "error")
                    return redirect(url_for("registration.my_registration"))
                # Usuwanie zgłoszenia przy ostatniej dyscyplinie
                if not kumite_id:
                    cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (reg_id,))
                    flash("Twoje zgłoszenie zostało wycofane (była to jedyna dyscyplina).", "success")
                else:
                    cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kata_id = NULL WHERE id = %s", (reg_id,))
                    flash("Zostałeś wycofany z Kata.", "success")
            else:  # kumite
                if not kumite_id:
                    flash("Nie jesteś zapisany do Kumite w tym zgłoszeniu.", "error")
                    return redirect(url_for("registration.my_registration"))
                # Usuwanie zgłoszenia przy ostatniej dyscyplinie
                if not kata_id:
                    cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (reg_id,))
                    flash("Twoje zgłoszenie zostało wycofane (była to jedyna dyscyplina).", "success")
                else:
                    cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kumite_id = NULL WHERE id = %s", (reg_id,))
                    flash("Zostałeś wycofany z Kumite.", "success")

            conn.commit()
            return redirect(url_for("registration.my_registration"))

    except Exception as e:
        flash(f"Błąd podczas wycofywania dyscypliny: {e}", "error")
        return redirect(url_for("registration.my_registration"))

