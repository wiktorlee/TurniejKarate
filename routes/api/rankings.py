from flask import Blueprint, jsonify
from collections import defaultdict
from database import get_conn
from config import SCHEMA

api_rankings_bp = Blueprint('api_rankings', __name__)


# GET /api/rankings - pobierz rankingi
@api_rankings_bp.get("/api/rankings")
def get_rankings():
    club_ranking = []
    nation_ranking = []
    individual_ranking = defaultdict(list)

    try:
        with get_conn() as conn, conn.cursor() as cur:
            # 1. Ranking Klubowy
            cur.execute(f"""
                SELECT club_name, SUM(points) as total_points
                FROM {SCHEMA}.v_results_with_users
                WHERE club_name IS NOT NULL AND club_name != ''
                GROUP BY club_name
                ORDER BY total_points DESC
            """)
            club_rows = cur.fetchall()
            for idx, row in enumerate(club_rows, 1):
                club_ranking.append({"place": idx, "name": row[0], "points": row[1]})

            # 2. Ranking Narodowościowy
            cur.execute(f"""
                SELECT country_code, SUM(points) as total_points
                FROM {SCHEMA}.v_results_with_users
                WHERE country_code IS NOT NULL
                GROUP BY country_code
                ORDER BY total_points DESC
            """)
            nation_rows = cur.fetchall()
            for idx, row in enumerate(nation_rows, 1):
                nation_ranking.append({"place": idx, "name": row[0], "points": row[1]})

            # 3. Ranking Indywidualny per Kategoria
            cur.execute(f"""
                SELECT category_name, 
                       first_name, last_name, club_name, country_code,
                       SUM(points) as total_points
                FROM {SCHEMA}.v_results_with_users
                GROUP BY category_name, athlete_code, first_name, last_name, club_name, country_code
                ORDER BY category_name ASC, total_points DESC
            """)
            indiv_rows = cur.fetchall()

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

            # Dodaj miejsca wewnątrz każdej kategorii
            for cat in individual_ranking:
                for idx, player in enumerate(individual_ranking[cat], 1):
                    player["place"] = idx

            # Konwertuj defaultdict na dict dla JSON
            individual_ranking_dict = dict(individual_ranking)

            return jsonify({
                "club_ranking": club_ranking,
                "nation_ranking": nation_ranking,
                "individual_ranking": individual_ranking_dict
            })

    except Exception as e:
        return jsonify({"error": f"Błąd rankingu: {e}"}), 500

