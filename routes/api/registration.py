from flask import Blueprint, request, jsonify, session
from services.registration_service import RegistrationService
from services.competition_service import CompetitionService

api_registration_bp = Blueprint('api_registration', __name__)

# Inicjalizacja serwisów
registration_service = RegistrationService()
competition_service = CompetitionService()


# GET /api/my-registration - pobierz moje zgłoszenia
@api_registration_bp.get("/api/my-registration")
def get_my_registration():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany, aby zobaczyć swoje zgłoszenie."}), 401

    try:
        result = registration_service.get_my_registration(uid)
        
        if result.get("error"):
            return jsonify(result), 400
        
        return jsonify(result)
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
        result = registration_service.withdraw(uid, registration_id)
        
        if result.get("error"):
            return jsonify(result), 403
        
        return jsonify(result)
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
        result = registration_service.withdraw_discipline(uid, registration_id, discipline_type)
        
        if result.get("error"):
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas wycofywania dyscypliny: {e}"}), 500


# GET /api/kata/competitors/<event_id>/<category_kata_id> - lista zawodników Kata
@api_registration_bp.get("/api/kata/competitors/<int:event_id>/<int:category_kata_id>")
def kata_competitors(event_id, category_kata_id):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany."}), 401
    
    try:
        result = competition_service.get_kata_competitors(uid, event_id, category_kata_id)
        
        if result.get("error"):
            return jsonify(result), 404
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas pobierania listy zawodników: {e}"}), 500


# GET /api/kumite/bracket/<event_id>/<category_kumite_id> - drzewko walk Kumite
@api_registration_bp.get("/api/kumite/bracket/<int:event_id>/<int:category_kumite_id>")
def kumite_bracket(event_id, category_kumite_id):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Musisz być zalogowany."}), 401
    
    try:
        result = competition_service.get_kumite_bracket(uid, event_id, category_kumite_id)
        
        if result.get("error"):
            return jsonify(result), 404
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas pobierania drzewka walk: {e}"}), 500

