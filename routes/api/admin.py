from flask import Blueprint, request, jsonify, session
from functools import wraps
from services.user_service import UserService
from services.admin_service import AdminService

api_admin_bp = Blueprint('api_admin', __name__)

# Inicjalizacja serwisów
user_service = UserService()
admin_service = AdminService()


def require_admin_api(f):
    """Dekorator sprawdzający uprawnienia administratora dla API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get("user_id")
        if not uid:
            return jsonify({"error": "Musisz być zalogowany."}), 401
        
        if not user_service.is_admin(uid):
            return jsonify({"error": "Brak uprawnień administratora."}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# GET /api/admin/dashboard - panel admina
@api_admin_bp.get("/api/admin/dashboard")
@require_admin_api
def get_dashboard():
    try:
        data = admin_service.get_dashboard()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas ładowania panelu: {e}"}), 500


# POST /api/admin/restore-dummy-athletes - zarejestruj kukiełki
@api_admin_bp.post("/api/admin/restore-dummy-athletes")
@require_admin_api
def restore_dummy_athletes():
    try:
        result = admin_service.restore_dummy_athletes()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas rejestracji kukiełek: {e}"}), 500


# POST /api/admin/reset - reset systemu
@api_admin_bp.post("/api/admin/reset")
@require_admin_api
def reset_system():
    data = request.get_json()
    restore_dummies = data.get("restore_dummies", False)
    
    try:
        result = admin_service.reset_system(restore_dummies)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas resetu: {e}"}), 500


# POST /api/admin/simulate - symulacja sezonu
@api_admin_bp.post("/api/admin/simulate")
@require_admin_api
def simulate_season():
    try:
        result = admin_service.simulate_season()
        
        if result.get("error"):
            return jsonify(result), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Błąd podczas symulacji: {e}"}), 500

