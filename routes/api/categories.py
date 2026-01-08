from flask import Blueprint, request, jsonify, session
from services.category_service import CategoryService

api_categories_bp = Blueprint('api_categories', __name__)

# Inicjalizacja serwisu
category_service = CategoryService()


# GET /api/categories - pobierz listę eventów, dyscyplin i kategorii
@api_categories_bp.get("/api/categories")
def get_categories():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany, aby zobaczyć kategorie."}), 401

    try:
        result = category_service.get_categories(uid)
        
        if result.get("error"):
            status_code = 403 if "system_status" in result else 400
            return jsonify(result), status_code
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Wystąpił błąd bazy danych: {e}"}), 500


# POST /api/categories/register - rejestracja na kategorię
@api_categories_bp.post("/api/categories/register")
def register_to_category():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany."}), 401

    data = request.get_json()
    
    try:
        result = category_service.register_to_category(uid, data)
        
        if result.get("error"):
            status_code = 409 if "UniqueViolation" in result["error"] else (
                403 if "zakończonym" in result["error"] else (
                    404 if "Nie znaleziono" in result["error"] else 400
                )
            )
            return jsonify(result), status_code
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Wystąpił błąd bazy danych: {e}"}), 500

