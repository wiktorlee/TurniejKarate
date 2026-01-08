from flask import Blueprint, jsonify
from services.ranking_service import RankingService

api_rankings_bp = Blueprint('api_rankings', __name__)

# Inicjalizacja serwisu
ranking_service = RankingService()


# GET /api/rankings - pobierz rankingi
@api_rankings_bp.get("/api/rankings")
def get_rankings():
    try:
        result = ranking_service.get_rankings()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd rankingu: {e}"}), 500

