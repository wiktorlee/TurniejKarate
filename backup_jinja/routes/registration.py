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
                SELECT id, event_id, category_kata_id, category_kumite_id,
                       event_name, start_date, end_date,
                       kata_name, kumite_name
                FROM {SCHEMA}.v_user_registrations
                WHERE athlete_code = %s
                ORDER BY start_date, event_name
            """
            cur.execute(sql, (athlete_code,))
            rows = cur.fetchall()

            registrations = []
            for row in rows:
                reg_id, event_id, category_kata_id, category_kumite_id = row[0], row[1], row[2], row[3]
                
                # Pobierz wyniki dla Kata (jeśli istnieje)
                kata_result = None
                if category_kata_id:
                    # Pobierz nazwę kategorii Kata
                    cur.execute(f"""
                        SELECT name FROM {SCHEMA}.categories_kata WHERE id = %s
                    """, (category_kata_id,))
                    kata_cat_row = cur.fetchone()
                    if kata_cat_row:
                        kata_category_name = kata_cat_row[0]
                        cur.execute(f"""
                            SELECT place, points
                            FROM {SCHEMA}.results
                            WHERE athlete_code = %s 
                              AND event_id = %s 
                              AND category_name = %s
                            LIMIT 1
                        """, (athlete_code, event_id, kata_category_name))
                        kata_row = cur.fetchone()
                        if kata_row:
                            kata_result = {"place": kata_row[0], "points": kata_row[1]}
                
                # Pobierz wyniki dla Kumite (jeśli istnieje)
                kumite_result = None
                if category_kumite_id:
                    # Pobierz nazwę kategorii Kumite
                    cur.execute(f"""
                        SELECT name FROM {SCHEMA}.categories_kumite WHERE id = %s
                    """, (category_kumite_id,))
                    kumite_cat_row = cur.fetchone()
                    if kumite_cat_row:
                        kumite_category_name = kumite_cat_row[0]
                        cur.execute(f"""
                            SELECT place, points
                            FROM {SCHEMA}.results
                            WHERE athlete_code = %s 
                              AND event_id = %s 
                              AND category_name = %s
                            LIMIT 1
                        """, (athlete_code, event_id, kumite_category_name))
                        kumite_row = cur.fetchone()
                        if kumite_row:
                            kumite_result = {"place": kumite_row[0], "points": kumite_row[1]}
                
                registrations.append({
                    "reg_id": reg_id,
                    "event_id": event_id,
                    "category_kata_id": category_kata_id,
                    "category_kumite_id": category_kumite_id,
                    "event_name": row[4],
                    "start_date": row[5],
                    "end_date": row[6],
                    "kata_name": row[7],
                    "kumite_name": row[8],
                    "kata_result": kata_result,
                    "kumite_result": kumite_result
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
            try:
                conn.execute("BEGIN")
                
                if discipline_type == "kata":
                    if not kata_id:
                        conn.rollback()
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
                        conn.rollback()
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
                conn.rollback()
                flash(f"Błąd podczas wycofywania dyscypliny: {e}", "error")
                return redirect(url_for("registration.my_registration"))

    except Exception as e:
        flash(f"Błąd podczas wycofywania dyscypliny: {e}", "error")
        return redirect(url_for("registration.my_registration"))


#Lista zawodników Kata
@registration_bp.get("/kata/competitors/<int:event_id>/<int:category_kata_id>")
def kata_competitors(event_id, category_kata_id):
    """
    Wyświetla listę zawodników zapisanych do kategorii Kata.
    Weryfikuje czy użytkownik jest zalogowany (nie wymaga zapisu do kategorii).
    """
    uid = session.get("user_id")
    if not uid:
        flash("Musisz być zalogowany.", "error")
        return redirect(url_for("auth.login"))
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Pobierz athlete_code użytkownika (do wyróżnienia w liście)
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            user_row = cur.fetchone()
            user_athlete_code = user_row[0] if user_row and user_row[0] else None
            
            # Pobierz informacje o evencie i kategorii z widoku
            cur.execute(f"""
                SELECT DISTINCT event_name, event_start_date, event_end_date, category_name
                FROM {SCHEMA}.v_kata_competitors
                WHERE event_id = %s AND category_kata_id = %s
                LIMIT 1
            """, (event_id, category_kata_id))
            event_cat = cur.fetchone()
            if not event_cat:
                flash("Nie znaleziono eventu lub kategorii.", "error")
                return redirect(url_for("registration.my_registration"))
            
            event_name, start_date, end_date, category_name = event_cat
            
            # Pobierz listę zawodników z widoku (z wynikami)
            cur.execute(f"""
                SELECT athlete_code, first_name, last_name, 
                       country_code, club_name, nationality,
                       place, points
                FROM {SCHEMA}.v_kata_competitors
                WHERE event_id = %s AND category_kata_id = %s
                ORDER BY 
                    CASE WHEN place IS NULL THEN 999 ELSE place END,
                    last_name, first_name, athlete_code
            """, (event_id, category_kata_id))
            competitors = cur.fetchall()
            
            # Formatuj dane
            competitors_list = []
            for row in competitors:
                is_current_user = (row[0] == user_athlete_code)
                competitors_list.append({
                    "athlete_code": row[0],
                    "first_name": row[1] or "",
                    "last_name": row[2] or "",
                    "country_code": row[3],
                    "club_name": row[4] or "",
                    "nationality": row[5] or "",
                    "place": row[6],  # może być None
                    "points": row[7],  # może być None
                    "is_current_user": is_current_user
                })
            
            return render_template("kata_competitors.html",
                                 event_name=event_name,
                                 category_name=category_name,
                                 start_date=start_date,
                                 end_date=end_date,
                                 competitors=competitors_list,
                                 event_id=event_id)
    except Exception as e:
        flash(f"Błąd podczas pobierania listy zawodników: {e}", "error")
        return redirect(url_for("registration.my_registration"))


#Drzewko walk Kumite
@registration_bp.get("/kumite/bracket/<int:event_id>/<int:category_kumite_id>")
def kumite_bracket(event_id, category_kumite_id):
    """
    Wyświetla drzewko walk dla kategorii Kumite.
    Automatycznie generuje pojedynki jeśli nie istnieją.
    """
    uid = session.get("user_id")
    if not uid:
        flash("Musisz być zalogowany.", "error")
        return redirect(url_for("auth.login"))
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Pobierz athlete_code użytkownika
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            user_row = cur.fetchone()
            user_athlete_code = user_row[0] if user_row and user_row[0] else None
            
            # Pobierz informacje o evencie i kategorii z widoku
            cur.execute(f"""
                SELECT DISTINCT event_name, event_start_date, event_end_date, category_name
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
                LIMIT 1
            """, (event_id, category_kumite_id))
            event_cat = cur.fetchone()
            if not event_cat:
                flash("Nie znaleziono eventu lub kategorii.", "error")
                return redirect(url_for("registration.my_registration"))
            
            event_name, start_date, end_date, category_name = event_cat
            
            # Pobierz listę wszystkich zarejestrowanych zawodników z widoku
            cur.execute(f"""
                SELECT athlete_code
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
            """, (event_id, category_kumite_id))
            registered_athletes = set(row[0] for row in cur.fetchall())
            
            # Sprawdź czy istnieją pojedynki dla tej kategorii
            cur.execute(f"""
                SELECT COUNT(*) FROM {SCHEMA}.draw_fight 
                WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
            """, (category_kumite_id, event_id))
            fights_count = cur.fetchone()[0]
            
            # Pobierz listę zawodników w drzewku (jeśli istnieje)
            athletes_in_bracket = set()
            if fights_count > 0:
                cur.execute(f"""
                    SELECT DISTINCT red_code, blue_code
                    FROM {SCHEMA}.draw_fight
                    WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
                """, (category_kumite_id, event_id))
                for row in cur.fetchall():
                    if row[0]:  # red_code
                        athletes_in_bracket.add(row[0])
                    if row[1]:  # blue_code
                        athletes_in_bracket.add(row[1])
            
            # Jeśli brak pojedynków LUB zawodnicy w drzewku nie pasują do zarejestrowanych, wygeneruj/odśwież drzewka
            if fights_count == 0 or registered_athletes != athletes_in_bracket:
                # Usuń stare drzewka jeśli istnieją
                if fights_count > 0:
                    cur.execute(f"""
                        DELETE FROM {SCHEMA}.draw_fight 
                        WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
                    """, (category_kumite_id, event_id))
                    conn.commit()
                
                # Wygeneruj nowe drzewka
                if len(registered_athletes) >= 2:
                    _generate_kumite_bracket(conn, cur, event_id, category_kumite_id)
                    # Po wygenerowaniu, pobierz ponownie liczbę
                    cur.execute(f"""
                        SELECT COUNT(*) FROM {SCHEMA}.draw_fight 
                        WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
                    """, (category_kumite_id, event_id))
                    fights_count = cur.fetchone()[0]
            
            # Pobierz wszystkie rundy bezpośrednio z draw_fight (z wynikami)
            cur.execute(f"""
                SELECT df.round_no, df.fight_no, df.red_code, df.blue_code,
                       COALESCE(red_u.first_name, '') as red_first, 
                       COALESCE(red_u.last_name, '') as red_last,
                       red_u.country_code as red_country,
                       red_u.club_name as red_club,
                       COALESCE(blue_u.first_name, '') as blue_first,
                       COALESCE(blue_u.last_name, '') as blue_last,
                       blue_u.country_code as blue_country,
                       blue_u.club_name as blue_club,
                       df.winner_code, df.red_score, df.blue_score, 
                       COALESCE(df.is_finished, FALSE) as is_finished
                FROM {SCHEMA}.draw_fight df
                LEFT JOIN {SCHEMA}.users red_u ON df.red_code = red_u.athlete_code
                LEFT JOIN {SCHEMA}.users blue_u ON df.blue_code = blue_u.athlete_code
                WHERE df.category_kumite_id = %s AND df.event_id = %s
                ORDER BY df.round_no, df.fight_no
            """, (category_kumite_id, event_id))
            fights = cur.fetchall()
            
            # Utwórz płaską listę walk (szablon oczekuje fights_list)
            fights_list = []
            for row in fights:
                fight_no, red_code, blue_code = row[1], row[2], row[3]
                is_user_in_fight = (red_code == user_athlete_code or blue_code == user_athlete_code)
                
                fights_list.append({
                    "fight_no": fight_no,
                    "red_code": red_code,
                    "blue_code": blue_code,
                    "red_name": f"{row[4] or ''} {row[5] or ''}".strip() if row[4] or row[5] else "BYE",
                    "red_country": row[6] or "",
                    "red_club": row[7] or "",
                    "blue_name": f"{row[8] or ''} {row[9] or ''}".strip() if row[8] or row[9] else "BYE",
                    "blue_country": row[10] or "",
                    "blue_club": row[11] or "",
                    "winner_code": row[12],  # może być None
                    "red_score": row[13],  # może być None
                    "blue_score": row[14],  # może być None
                    "is_finished": row[15] if row[15] is not None else False,
                    "is_bye": (blue_code is None),
                    "is_current_user": is_user_in_fight
                })
            
            return render_template("kumite_bracket.html",
                                 event_name=event_name,
                                 category_name=category_name,
                                 start_date=start_date,
                                 end_date=end_date,
                                 fights_list=fights_list,
                                 event_id=event_id,
                                 category_kumite_id=category_kumite_id)
    except Exception as e:
        flash(f"Błąd podczas pobierania drzewka walk: {e}", "error")
        return redirect(url_for("registration.my_registration"))


def _generate_kumite_bracket(conn, cur, event_id, category_kumite_id):
    """
    Funkcja pomocnicza do generowania drzewka walk.
    Losowo przydziela zawodników do pojedynków.
    """
    # Pobierz zawodników zapisanych do kategorii z widoku - LOSOWO
    cur.execute(f"""
        SELECT athlete_code
        FROM {SCHEMA}.v_kumite_competitors
        WHERE event_id = %s AND category_kumite_id = %s
        ORDER BY RANDOM()
    """, (event_id, category_kumite_id))
    athletes = [row[0] for row in cur.fetchall()]
    
    if len(athletes) < 2:
        raise ValueError("Za mało zawodników do utworzenia drzewka (min. 2)")
    
    # Losowanie odbywa się już w SQL (ORDER BY RANDOM()), nie trzeba shuffle
    
    # Jeśli nieparzysta liczba, ostatni zawodnik dostaje BYE
    if len(athletes) % 2 != 0:
        athletes.append(None)  # None oznacza BYE
    
    # Utwórz pary i wstaw do draw_fight
    # category_id jest wymagane (NOT NULL), więc używamy category_kumite_id jako wartości
    try:
        conn.execute("BEGIN")
        
        fight_no = 1
        for i in range(0, len(athletes), 2):
            red_code = athletes[i]
            blue_code = athletes[i + 1] if i + 1 < len(athletes) else None
            
            cur.execute(f"""
                INSERT INTO {SCHEMA}.draw_fight 
                (category_id, category_kumite_id, event_id, round_no, fight_no, red_code, blue_code)
                VALUES (%s, %s, %s, 1, %s, %s, %s)
            """, (category_kumite_id, category_kumite_id, event_id, fight_no, red_code, blue_code))
            fight_no += 1
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
