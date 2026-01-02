from flask import Blueprint, request, jsonify, session
from database import get_conn
from config import SCHEMA

api_registration_bp = Blueprint('api_registration', __name__)


# GET /api/my-registration - pobierz moje zgłoszenia
@api_registration_bp.get("/api/my-registration")
def get_my_registration():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany, aby zobaczyć swoje zgłoszenie."}), 401

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                return jsonify({"error": "Nie masz przypisanego kodu zawodnika."}), 400
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
                
                # Pobierz wyniki dla Kata
                kata_result = None
                if category_kata_id:
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
                
                # Pobierz wyniki dla Kumite
                kumite_result = None
                if category_kumite_id:
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
                    "start_date": row[5].isoformat() if row[5] else None,
                    "end_date": row[6].isoformat() if row[6] else None,
                    "kata_name": row[7],
                    "kumite_name": row[8],
                    "kata_result": kata_result,
                    "kumite_result": kumite_result
                })

            return jsonify({"registrations": registrations})
    except Exception as e:
        return jsonify({"error": f"Błąd podczas pobierania zgłoszenia: {e}"}), 500


# DELETE /api/withdraw - wycofaj całkowicie zgłoszenie
@api_registration_bp.delete("/api/withdraw")
def withdraw():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji."}), 401

    data = request.get_json()
    registration_id = data.get("registration_id")
    if not registration_id:
        return jsonify({"error": "Brak ID zgłoszenia."}), 400

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                return jsonify({"error": "Nie masz przypisanego kodu zawodnika."}), 400
            athlete_code = row[0]

            # Weryfikacja przynależności
            cur.execute(f"SELECT id FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            reg = cur.fetchone()
            if not reg:
                return jsonify({"error": "Nie znaleziono zgłoszenia lub nie masz uprawnień do jego usunięcia."}), 403

            cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            conn.commit()
            return jsonify({"success": True, "message": "Twoje zgłoszenie zostało wycofane."})
    except Exception as e:
        return jsonify({"error": f"Błąd podczas wycofywania zgłoszenia: {e}"}), 500


# DELETE /api/withdraw-discipline - wycofaj pojedynczą dyscyplinę
@api_registration_bp.delete("/api/withdraw-discipline")
def withdraw_discipline():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji."}), 401

    data = request.get_json()
    registration_id = data.get("registration_id")
    discipline_type = data.get("discipline_type")
    
    if not registration_id:
        return jsonify({"error": "Brak ID zgłoszenia."}), 400
    if discipline_type not in ("kata", "kumite"):
        return jsonify({"error": "Nieprawidłowy typ dyscypliny."}), 400

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                return jsonify({"error": "Nie masz przypisanego kodu zawodnika."}), 400
            athlete_code = row[0]

            # Weryfikacja istnienia zgłoszenia
            cur.execute(f"SELECT id, category_kata_id, category_kumite_id FROM {SCHEMA}.registrations WHERE id = %s AND athlete_code = %s", (registration_id, athlete_code))
            reg = cur.fetchone()
            if not reg:
                return jsonify({"error": "Nie masz aktywnego zgłoszenia lub nie masz uprawnień."}), 403

            reg_id, kata_id, kumite_id = reg

            try:
                conn.execute("BEGIN")
                
                if discipline_type == "kata":
                    if not kata_id:
                        conn.rollback()
                        return jsonify({"error": "Nie jesteś zapisany do Kata w tym zgłoszeniu."}), 400
                    if not kumite_id:
                        cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (reg_id,))
                        message = "Twoje zgłoszenie zostało wycofane (była to jedyna dyscyplina)."
                    else:
                        cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kata_id = NULL WHERE id = %s", (reg_id,))
                        message = "Zostałeś wycofany z Kata."
                else:  # kumite
                    if not kumite_id:
                        conn.rollback()
                        return jsonify({"error": "Nie jesteś zapisany do Kumite w tym zgłoszeniu."}), 400
                    if not kata_id:
                        cur.execute(f"DELETE FROM {SCHEMA}.registrations WHERE id = %s", (reg_id,))
                        message = "Twoje zgłoszenie zostało wycofane (była to jedyna dyscyplina)."
                    else:
                        cur.execute(f"UPDATE {SCHEMA}.registrations SET category_kumite_id = NULL WHERE id = %s", (reg_id,))
                        message = "Zostałeś wycofany z Kumite."

                conn.commit()
                return jsonify({"success": True, "message": message})
            except Exception as e:
                conn.rollback()
                return jsonify({"error": f"Błąd podczas wycofywania dyscypliny: {e}"}), 500

    except Exception as e:
        return jsonify({"error": f"Błąd podczas wycofywania dyscypliny: {e}"}), 500


# GET /api/kata/competitors/<event_id>/<category_kata_id> - lista zawodników Kata
@api_registration_bp.get("/api/kata/competitors/<int:event_id>/<int:category_kata_id>")
def kata_competitors(event_id, category_kata_id):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany."}), 401
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            user_row = cur.fetchone()
            user_athlete_code = user_row[0] if user_row and user_row[0] else None
            
            cur.execute(f"""
                SELECT DISTINCT event_name, event_start_date, event_end_date, category_name
                FROM {SCHEMA}.v_kata_competitors
                WHERE event_id = %s AND category_kata_id = %s
                LIMIT 1
            """, (event_id, category_kata_id))
            event_cat = cur.fetchone()
            if not event_cat:
                return jsonify({"error": "Nie znaleziono eventu lub kategorii."}), 404
            
            event_name, start_date, end_date, category_name = event_cat
            
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
                    "place": row[6],
                    "points": row[7],
                    "is_current_user": is_current_user
                })
            
            return jsonify({
                "event_name": event_name,
                "category_name": category_name,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "competitors": competitors_list,
                "event_id": event_id
            })
    except Exception as e:
        return jsonify({"error": f"Błąd podczas pobierania listy zawodników: {e}"}), 500


# GET /api/kumite/bracket/<event_id>/<category_kumite_id> - drzewko walk Kumite
@api_registration_bp.get("/api/kumite/bracket/<int:event_id>/<int:category_kumite_id>")
def kumite_bracket(event_id, category_kumite_id):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany."}), 401
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT athlete_code FROM {SCHEMA}.users WHERE id = %s", (uid,))
            user_row = cur.fetchone()
            user_athlete_code = user_row[0] if user_row and user_row[0] else None
            
            cur.execute(f"""
                SELECT DISTINCT event_name, event_start_date, event_end_date, category_name
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
                LIMIT 1
            """, (event_id, category_kumite_id))
            event_cat = cur.fetchone()
            if not event_cat:
                return jsonify({"error": "Nie znaleziono eventu lub kategorii."}), 404
            
            event_name, start_date, end_date, category_name = event_cat
            
            # Pobierz listę zarejestrowanych zawodników
            cur.execute(f"""
                SELECT athlete_code
                FROM {SCHEMA}.v_kumite_competitors
                WHERE event_id = %s AND category_kumite_id = %s
            """, (event_id, category_kumite_id))
            registered_athletes = set(row[0] for row in cur.fetchall())
            
            # Sprawdź czy istnieją pojedynki
            cur.execute(f"""
                SELECT COUNT(*) FROM {SCHEMA}.draw_fight 
                WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
            """, (category_kumite_id, event_id))
            fights_count = cur.fetchone()[0]
            
            # Pobierz listę zawodników w drzewku
            athletes_in_bracket = set()
            if fights_count > 0:
                cur.execute(f"""
                    SELECT DISTINCT red_code, blue_code
                    FROM {SCHEMA}.draw_fight
                    WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
                """, (category_kumite_id, event_id))
                for row in cur.fetchall():
                    if row[0]:
                        athletes_in_bracket.add(row[0])
                    if row[1]:
                        athletes_in_bracket.add(row[1])
            
            # Wygeneruj/odśwież drzewka jeśli potrzeba
            if fights_count == 0 or registered_athletes != athletes_in_bracket:
                if fights_count > 0:
                    cur.execute(f"""
                        DELETE FROM {SCHEMA}.draw_fight 
                        WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
                    """, (category_kumite_id, event_id))
                    conn.commit()
                
                if len(registered_athletes) >= 2:
                    _generate_kumite_bracket(conn, cur, event_id, category_kumite_id)
                    cur.execute(f"""
                        SELECT COUNT(*) FROM {SCHEMA}.draw_fight 
                        WHERE category_kumite_id = %s AND event_id = %s AND round_no = 1
                    """, (category_kumite_id, event_id))
                    fights_count = cur.fetchone()[0]
            
            # Pobierz wszystkie rundy
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
                    "winner_code": row[12],
                    "red_score": row[13],
                    "blue_score": row[14],
                    "is_finished": row[15] if row[15] is not None else False,
                    "is_bye": (blue_code is None),
                    "is_current_user": is_user_in_fight
                })
            
            return jsonify({
                "event_name": event_name,
                "category_name": category_name,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "fights_list": fights_list,
                "event_id": event_id,
                "category_kumite_id": category_kumite_id
            })
    except Exception as e:
        return jsonify({"error": f"Błąd podczas pobierania drzewka walk: {e}"}), 500


def _generate_kumite_bracket(conn, cur, event_id, category_kumite_id):
    """Funkcja pomocnicza do generowania drzewka walk."""
    cur.execute(f"""
        SELECT athlete_code
        FROM {SCHEMA}.v_kumite_competitors
        WHERE event_id = %s AND category_kumite_id = %s
        ORDER BY RANDOM()
    """, (event_id, category_kumite_id))
    athletes = [row[0] for row in cur.fetchall()]
    
    if len(athletes) < 2:
        raise ValueError("Za mało zawodników do utworzenia drzewka (min. 2)")
    
    if len(athletes) % 2 != 0:
        athletes.append(None)
    
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

