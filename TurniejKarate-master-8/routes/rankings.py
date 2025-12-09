from flask import Blueprint, render_template, flash, redirect, url_for
from collections import defaultdict
from database import get_conn
from config import SCHEMA

rankings_bp = Blueprint('rankings', __name__)

@rankings_bp.route("/rankings", methods=["GET"])
def show_rankings():
    club_ranking = []
    nation_ranking = []
    # Słownik do rankingu indywidualnego:
    # Klucz = Nazwa kategorii, Wartość = Lista zawodników
    individual_ranking = defaultdict(list)

    try:
        with get_conn() as conn, conn.cursor() as cur:
            # 1. Ranking Klubowy (bez zmian)
            cur.execute(f"""
                SELECT u.club_name, SUM(r.points) as total_points
                FROM {SCHEMA}.results r
                JOIN {SCHEMA}.users u ON r.athlete_code = u.athlete_code
                WHERE u.club_name IS NOT NULL AND u.club_name != ''
                GROUP BY u.club_name
                ORDER BY total_points DESC
            """)
            club_rows = cur.fetchall()
            for idx, row in enumerate(club_rows, 1):
                club_ranking.append({"place": idx, "name": row[0], "points": row[1]})

            # 2. Ranking Narodowościowy (bez zmian)
            cur.execute(f"""
                SELECT u.country_code, SUM(r.points) as total_points
                FROM {SCHEMA}.results r
                JOIN {SCHEMA}.users u ON r.athlete_code = u.athlete_code
                WHERE u.country_code IS NOT NULL
                GROUP BY u.country_code
                ORDER BY total_points DESC
            """)
            nation_rows = cur.fetchall()
            for idx, row in enumerate(nation_rows, 1):
                nation_ranking.append({"place": idx, "name": row[0], "points": row[1]})

            # 3. NOWOŚĆ: Ranking Indywidualny per Kategoria
            # Pobieramy: Kategorię, Imię, Nazwisko, Klub, Sumę punktów w tej kategorii
            cur.execute(f"""
                SELECT r.category_name, 
                       u.first_name, u.last_name, u.club_name, u.country_code,
                       SUM(r.points) as total_points
                FROM {SCHEMA}.results r
                JOIN {SCHEMA}.users u ON r.athlete_code = u.athlete_code
                GROUP BY r.category_name, u.id
                ORDER BY r.category_name ASC, total_points DESC
            """)
            indiv_rows = cur.fetchall()

            # Grupujemy wyniki w Pythonie według kategorii
            for row in indiv_rows:
                cat_name = row[0]
                player_data = {
                    "first_name": row[1],
                    "last_name": row[2],
                    "club": row[3],
                    "country": row[4],
                    "points": row[5]
                }
                individual_ranking[cat_name].append(player_data)

            # Dodajemy miejsca (1, 2, 3...) wewnątrz każdej kategorii
            for cat in individual_ranking:
                for idx, player in enumerate(individual_ranking[cat], 1):
                    player["place"] = idx

    except Exception as e:
        flash(f"Błąd rankingu: {e}", "error")
        return redirect(url_for("main.index"))

    return render_template("rankings.html",
                         club_ranking=club_ranking,
                         nation_ranking=nation_ranking,
                         individual_ranking=individual_ranking)