from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from datetime import date
import psycopg.errors
from database import get_conn
from config import SCHEMA

categories_bp = Blueprint('categories', __name__)


#Kategorie
@categories_bp.route("/categories", methods=["GET", "POST"])
def categories():
    uid = session.get("user_id")
    if not uid:
        flash("Musisz być zalogowany, aby zobaczyć kategorie.", "error")
        return redirect(url_for("auth.login"))

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Nie masz przypisanego kodu zawodnika.", "error")
                return redirect(url_for("profile.profile"))
            athlete_code = row[0]

            #czy już jest zgłoszenie
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE athlete_code=%s", (athlete_code,))
            if cur.fetchone():
                flash("Jesteś już zapisany do kategorii. Możesz wycofać swoje zgłoszenie w 'Moje zgłoszenie'.", "info")
                return redirect(url_for("registration.my_registration"))


            if request.method == "POST":
                category_id = request.form.get("category_id")
                if not category_id:
                    flash("Nie wybrano kategorii.", "error")
                    return redirect(url_for("categories.categories"))

                # dane zawodnika
                cur.execute(f"SELECT sex, birth_date, weight FROM {SCHEMA}.users WHERE id=%s", (uid,))
                user_data = cur.fetchone()
                if not user_data:
                    flash("Nie znaleziono danych użytkownika.", "error")
                    return redirect(url_for("categories.categories"))
                user_sex, birth_date, weight = user_data

                # dane kategorii
                cur.execute(f"""
                    SELECT name, sex, min_age, max_age, min_weight, max_weight
                    FROM {SCHEMA}.categories
                    WHERE id = %s
                """, (category_id,))
                cat = cur.fetchone()
                if not cat:
                    flash("Nie znaleziono kategorii.", "error")
                    return redirect(url_for("categories.categories"))
                cat_name, cat_sex, min_age, max_age, min_weight, max_weight = cat

                # Walidacje
                # płeć
                if user_sex != cat_sex:
                    flash(f"Nie możesz zapisać się do kategorii {cat_name} (inna płeć).", "error")
                    return redirect(url_for("categories.categories"))

                # wiek
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                if min_age and age < min_age:
                    flash(f"Za młody do tej kategorii ({age} lat, wymagane min {min_age}).", "error")
                    return redirect(url_for("categories.categories"))
                if max_age and age > max_age:
                    flash(f"Za stary do tej kategorii ({age} lat, dopuszczalne max {max_age}).", "error")
                    return redirect(url_for("categories.categories"))

                # waga
                if min_weight and weight < min_weight:
                    flash(f"Za lekki na tę kategorię (min {min_weight} kg).", "error")
                    return redirect(url_for("categories.categories"))
                if max_weight and weight > max_weight:
                    flash(f"Za ciężki na tę kategorię (max {max_weight} kg).", "error")
                    return redirect(url_for("categories.categories"))

                # zapis jeśli wszystko OK
                cur.execute(f"INSERT INTO {SCHEMA}.registrations (athlete_code, category_id) VALUES (%s, %s)",
                            (athlete_code, category_id))
                conn.commit()
                flash("Zostałeś pomyślnie zapisany na zawody!", "success")
                return redirect(url_for("registration.my_registration"))

            # GET → lista kategorii
            cur.execute(f"SELECT id, name FROM {SCHEMA}.categories ORDER BY name")
            cats = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
            return render_template("categories.html", categories=cats)

    except psycopg.errors.UniqueViolation:
        flash("Błąd: Jesteś już zapisany (UniqueViolation).", "error")
        return redirect(url_for("registration.my_registration"))
    except Exception as e:
        flash(f"Wystąpił błąd bazy danych: {e}", "error")
        return redirect(url_for("profile.profile"))

