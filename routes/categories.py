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
            cur.execute(f"SELECT athlete_code, sex, birth_date, weight FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Nie masz przypisanego kodu zawodnika.", "error")
                return redirect(url_for("profile.profile"))
            athlete_code, user_sex, birth_date, weight = row[0], row[1], row[2], row[3]

            if request.method == "POST":
                event_id = request.form.get("event_id")
                discipline_kata = request.form.get("discipline_kata") == "on"
                discipline_kumite = request.form.get("discipline_kumite") == "on"
                category_kata_id = request.form.get("category_kata_id")
                category_kumite_id = request.form.get("category_kumite_id")

                if not event_id:
                    flash("Nie wybrano eventu.", "error")
                    return redirect(url_for("categories.categories"))

                if not discipline_kata and not discipline_kumite:
                    flash("Wybierz przynajmniej jedną dyscyplinę (Kata lub Kumite).", "error")
                    return redirect(url_for("categories.categories"))

                if discipline_kata and not category_kata_id:
                    flash("Wybierz kategorię dla Kata.", "error")
                    return redirect(url_for("categories.categories"))

                if discipline_kumite and not category_kumite_id:
                    flash("Wybierz kategorię dla Kumite.", "error")
                    return redirect(url_for("categories.categories"))

                # Walidacja wieku i wagi
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

                # Walidacja Kata
                if discipline_kata:
                    cur.execute(f"""
                        SELECT name, sex, min_age, max_age
                        FROM {SCHEMA}.categories_kata
                        WHERE id = %s AND is_active = true
                    """, (category_kata_id,))
                    kata_cat = cur.fetchone()
                    if not kata_cat:
                        flash("Nie znaleziono kategorii Kata.", "error")
                        return redirect(url_for("categories.categories"))
                    kata_name, kata_sex, kata_min_age, kata_max_age = kata_cat

                    if user_sex != kata_sex:
                        flash(f"Nie możesz zapisać się do kategorii Kata {kata_name} (inna płeć).", "error")
                        return redirect(url_for("categories.categories"))
                    if kata_min_age and age < kata_min_age:
                        flash(f"Za młody do kategorii Kata {kata_name} ({age} lat, wymagane min {kata_min_age}).", "error")
                        return redirect(url_for("categories.categories"))
                    if kata_max_age and age > kata_max_age:
                        flash(f"Za stary do kategorii Kata {kata_name} ({age} lat, dopuszczalne max {kata_max_age}).", "error")
                        return redirect(url_for("categories.categories"))

                # Walidacja Kumite
                if discipline_kumite:
                    cur.execute(f"""
                        SELECT name, sex, min_age, max_age, min_weight, max_weight
                        FROM {SCHEMA}.categories_kumite
                        WHERE id = %s AND is_active = true
                    """, (category_kumite_id,))
                    kumite_cat = cur.fetchone()
                    if not kumite_cat:
                        flash("Nie znaleziono kategorii Kumite.", "error")
                        return redirect(url_for("categories.categories"))
                    kumite_name, kumite_sex, kumite_min_age, kumite_max_age, kumite_min_weight, kumite_max_weight = kumite_cat

                    if user_sex != kumite_sex:
                        flash(f"Nie możesz zapisać się do kategorii Kumite {kumite_name} (inna płeć).", "error")
                        return redirect(url_for("categories.categories"))
                    if kumite_min_age and age < kumite_min_age:
                        flash(f"Za młody do kategorii Kumite {kumite_name} ({age} lat, wymagane min {kumite_min_age}).", "error")
                        return redirect(url_for("categories.categories"))
                    if kumite_max_age and age > kumite_max_age:
                        flash(f"Za stary do kategorii Kumite {kumite_name} ({age} lat, dopuszczalne max {kumite_max_age}).", "error")
                        return redirect(url_for("categories.categories"))
                    if kumite_min_weight and weight and weight < kumite_min_weight:
                        flash(f"Za lekki na kategorię Kumite {kumite_name} (min {kumite_min_weight} kg).", "error")
                        return redirect(url_for("categories.categories"))
                    if kumite_max_weight and weight and weight > kumite_max_weight:
                        flash(f"Za ciężki na kategorię Kumite {kumite_name} (max {kumite_max_weight} kg).", "error")
                        return redirect(url_for("categories.categories"))

                # Sprawdź czy już jest zgłoszenie
                cur.execute(f"SELECT id, event_id FROM {SCHEMA}.registrations WHERE athlete_code=%s", (athlete_code,))
                existing = cur.fetchone()

                # Pobierz discipline_id dla Kata lub Kumite
                discipline_id = None
                if discipline_kata and discipline_kumite:
                    # Jeśli obie dyscypliny, używamy pierwszej znalezionej (można to później poprawić)
                    cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kata' LIMIT 1")
                    disc_row = cur.fetchone()
                    if disc_row:
                        discipline_id = disc_row[0]
                elif discipline_kata:
                    cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kata' LIMIT 1")
                    disc_row = cur.fetchone()
                    if disc_row:
                        discipline_id = disc_row[0]
                elif discipline_kumite:
                    cur.execute(f"SELECT id FROM {SCHEMA}.disciplines WHERE name = 'Kumite' LIMIT 1")
                    disc_row = cur.fetchone()
                    if disc_row:
                        discipline_id = disc_row[0]

                if existing:
                    # Aktualizuj istniejące zgłoszenie
                    reg_id = existing[0]
                    cur.execute(f"""
                        UPDATE {SCHEMA}.registrations
                        SET event_id = %s, discipline_id = %s, category_kata_id = %s, category_kumite_id = %s
                        WHERE id = %s
                    """, (event_id, discipline_id, category_kata_id if discipline_kata else None, 
                          category_kumite_id if discipline_kumite else None, reg_id))
                    conn.commit()
                    flash("Zgłoszenie zostało zaktualizowane!", "success")
                else:
                    # Nowe zgłoszenie
                    cur.execute(f"""
                        INSERT INTO {SCHEMA}.registrations 
                        (athlete_code, event_id, discipline_id, category_kata_id, category_kumite_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (athlete_code, event_id, discipline_id, 
                          category_kata_id if discipline_kata else None,
                          category_kumite_id if discipline_kumite else None))
                    conn.commit()
                    flash("Zostałeś pomyślnie zapisany na zawody!", "success")
                return redirect(url_for("registration.my_registration"))

            # GET → pobierz dane do formularza
            cur.execute(f"SELECT id, name FROM {SCHEMA}.events WHERE is_active = true ORDER BY start_date, name")
            events = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            cur.execute(f"SELECT id, name FROM {SCHEMA}.disciplines ORDER BY name")
            disciplines = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            cur.execute(f"""
                SELECT id, name FROM {SCHEMA}.categories_kata 
                WHERE is_active = true AND sex = %s
                ORDER BY name
            """, (user_sex,))
            categories_kata = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            cur.execute(f"""
                SELECT id, name FROM {SCHEMA}.categories_kumite 
                WHERE is_active = true AND sex = %s
                ORDER BY name
            """, (user_sex,))
            categories_kumite = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # Sprawdź czy już jest zgłoszenie
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE athlete_code=%s", (athlete_code,))
            has_registration = cur.fetchone() is not None

            return render_template("categories.html", 
                                 events=events,
                                 disciplines=disciplines,
                                 categories_kata=categories_kata,
                                 categories_kumite=categories_kumite,
                                 has_registration=has_registration)

    except psycopg.errors.UniqueViolation:
        flash("Błąd: Jesteś już zapisany (UniqueViolation).", "error")
        return redirect(url_for("registration.my_registration"))
    except Exception as e:
        flash(f"Wystąpił błąd bazy danych: {e}", "error")
        return redirect(url_for("profile.profile"))

