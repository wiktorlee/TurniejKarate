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

    result = user_service.get_profile(uid)
    
    if result.get("error"):
        return jsonify(result), 404
    
    return jsonify(result)


# PUT /api/profile - aktualizuj profil użytkownika
@api_profile_bp.put("/api/profile")
def update_profile():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Brak sesji – zaloguj się albo zarejestruj."}), 401

    data = request.get_json()
    result = user_service.update_profile(uid, data)
    
    if result.get("error"):
        return jsonify(result), 400
    
    return jsonify(result)

