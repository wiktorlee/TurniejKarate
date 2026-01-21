from flask import Blueprint, request, jsonify, session
from services.user_service import UserService

api_profile_bp = Blueprint('api_profile', __name__)

# Inicjalizacja serwisu
user_service = UserService()


# GET /api/profile - pobierz profil użytkownika
@api_profile_bp.get("/api/profile")
def get_profile():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji – zaloguj się albo zarejestruj."}), 401

    try:
        result = user_service.get_profile(uid)
        
        if result.get("error"):
            return jsonify(result), 404
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas pobierania profilu: {str(e)}"}), 500


# PUT /api/profile - aktualizuj profil użytkownika
@api_profile_bp.put("/api/profile")
def update_profile():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji – zaloguj się albo zarejestruj."}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Brak danych w żądaniu"}), 400
        
        result = user_service.update_profile(uid, data)
        
        if result.get("error"):
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas aktualizacji profilu: {str(e)}"}), 500

