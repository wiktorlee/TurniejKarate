from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService
from services.club_service import ClubService

api_auth_bp = Blueprint('api_auth', __name__)

# Inicjalizacja serwisów
auth_service = AuthService()
club_service = ClubService()


# GET /api/clubs - pobierz listę klubów (do formularza rejestracji)
@api_auth_bp.get("/api/clubs")
def get_clubs_endpoint():
    """Zwraca listę klubów do formularza rejestracji"""
    clubs = club_service.get_all()
    return jsonify({"clubs": clubs})


# POST /api/register - rejestracja
@api_auth_bp.post("/api/register")
def register():
    data = request.get_json()
    result = auth_service.register(data)
    
    if result.get("error"):
        status_code = 409 if "już istnieje" in result["error"] else 400
        return jsonify(result), status_code
    
    # Ustawienie sesji
    session.clear()
    session["user_id"] = result["user_id"]
    session["login"] = data.get("login")
    
    return jsonify(result), 201


# POST /api/login - logowanie
@api_auth_bp.post("/api/login")
def login():
    data = request.get_json()
    
    login_val = (data.get("login") or "").strip()
    password_val = (data.get("password") or "").strip()

    if not login_val:
        return jsonify({"error": "Podaj login."}), 400
    if not password_val:
        return jsonify({"error": "Podaj hasło."}), 400

    result = auth_service.login(login_val, password_val)
    
    if result.get("error"):
        return jsonify(result), 401

    session.clear()
    session["user_id"] = result["user_id"]
    session["login"] = login_val
    session["is_admin"] = result["is_admin"]
    
    return jsonify(result)


# POST /api/logout - wylogowanie
@api_auth_bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Wylogowano."})


# GET /api/auth/check - sprawdź czy użytkownik jest zalogowany
@api_auth_bp.get("/api/auth/check")
def check_auth():
    """Sprawdza czy użytkownik jest zalogowany i zwraca podstawowe info o sesji"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200
    
    return jsonify({
        "authenticated": True,
        "user_id": user_id,
        "login": session.get("login"),
        "is_admin": session.get("is_admin", False)
    })

