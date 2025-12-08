from flask import Blueprint, render_template, flash, redirect, url_for
from database import get_conn
from config import SCHEMA

rankings_bp = Blueprint('rankings', __name__)


@rankings_bp.route("/rankings", methods=["GET"])
def show_rankings():
    """
    Wyświetla ranking klubowy i narodowościowy na podstawie sumy punktów
    z tabeli karate.results.
    """
    club_ranking = []
    nation_ranking = []

    try:
        with get_conn() as conn, conn.cursor() as cur:
            # 1. Ranking Klubowy
            # Łączymy wyniki z użytkownikami, grupujemy po klubie i sumujemy punkty
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
                club_ranking.append({
                    "place": idx,
                    "name": row[0],
                    "points": row[1]
                })

            # 2. Ranking Narodowościowy
            # Grupujemy po kodzie kraju (country_code)
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
                nation_ranking.append({
                    "place": idx,
                    "name": row[0],  # Np. POL, USA
                    "points": row[1]
                })

    except Exception as e:
        flash(f"Błąd podczas generowania rankingów: {e}", "error")
        return redirect(url_for("main.index"))

    return render_template("rankings.html",
                           club_ranking=club_ranking,
                           nation_ranking=nation_ranking)