from flask import Blueprint, request, jsonify, session
from database import get_conn
from config import SCHEMA
from functools import wraps

api_admin_bp = Blueprint('api_admin', __name__)


def require_admin_api(f):
    """Dekorator sprawdzający uprawnienia administratora dla API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get("user_id")
        if not uid:
            return jsonify({"error": "Musisz być zalogowany."}), 401
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT is_admin FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                return jsonify({"error": "Brak uprawnień administratora."}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# GET /api/admin/dashboard - panel admina
@api_admin_bp.get("/api/admin/dashboard")
@require_admin_api
def get_dashboard():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT status, simulation_date, reset_date, updated_at
                FROM {SCHEMA}.system_status 
                ORDER BY id DESC LIMIT 1
            """)
            status_row = cur.fetchone()
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.users WHERE is_dummy = true")
            dummy_count = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.events WHERE is_active = true")
            active_events = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.results")
            results_count = cur.fetchone()[0]
            
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.registrations")
            registrations_count = cur.fetchone()[0]
            
            system_status = {
                "status": status_row[0] if status_row else "ACTIVE",
                "simulation_date": status_row[1].isoformat() if status_row and status_row[1] else None,
                "reset_date": status_row[2].isoformat() if status_row and status_row[2] else None,
                "updated_at": status_row[3].isoformat() if status_row and status_row[3] else None
            }
            
            return jsonify({
                "system_status": system_status,
                "dummy_count": dummy_count,
                "active_events": active_events,
                "results_count": results_count,
                "registrations_count": registrations_count
            })
    except Exception as e:
        return jsonify({"error": f"Błąd podczas ładowania panelu: {e}"}), 500


# POST /api/admin/restore-dummy-athletes - zarejestruj kukiełki
@api_admin_bp.post("/api/admin/restore-dummy-athletes")
@require_admin_api
def restore_dummy_athletes():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
            results = cur.fetchall()
            
            total_registrations = sum(row[2] for row in results if isinstance(row[2], int)) if results else 0
            athletes_processed = len([r for r in results if r[2] and r[2] > 0]) if results else 0
            
            if total_registrations > 0:
                message = f"Pomyślnie zarejestrowano {total_registrations} zapisów dla {athletes_processed} kukiełek."
                return jsonify({"success": True, "message": message})
            else:
                if results and results[0][0] == 'Brak kukiełek do zarejestrowania':
                    message = "Brak kukiełek do zarejestrowania. Upewnij się, że istnieją użytkownicy z is_dummy=true i przypisanymi kategoriami."
                else:
                    message = "Brak nowych rejestracji do utworzenia. (Wszystkie kukiełki mogą być już zarejestrowane lub brak aktywnych eventów)"
                return jsonify({"success": True, "message": message, "info": True})
            
    except Exception as e:
        return jsonify({"error": f"Błąd podczas rejestracji kukiełek: {e}"}), 500


# POST /api/admin/reset - reset systemu
@api_admin_bp.post("/api/admin/reset")
@require_admin_api
def reset_system():
    data = request.get_json()
    restore_dummies = data.get("restore_dummies", False)
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            
            cur.execute(f"DELETE FROM {SCHEMA}.results")
            deleted_results = cur.rowcount
            
            cur.execute(f"DELETE FROM {SCHEMA}.draw_fight")
            deleted_fights = cur.rowcount
            
            restored_count = 0
            if restore_dummies:
                cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
                results = cur.fetchall()
                restored_count = sum(row[2] for row in results if isinstance(row[2], int)) if results else 0
            
            cur.execute(f"""
                UPDATE {SCHEMA}.system_status 
                SET status = 'ACTIVE', reset_date = now(), updated_at = now()
                WHERE id = (SELECT id FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1)
            """)
            
            conn.commit()
            
            msg = f"System zresetowany. Usunięto {deleted_results} wyników i {deleted_fights} walk."
            if restore_dummies:
                msg += f" Przywrócono {restored_count} rejestracji kukiełek."
            else:
                msg += " (Rejestracje kukiełek nie zostały przywrócone - użyj przycisku 'Zarejestruj kukiełki' jeśli potrzebujesz)"
            
            return jsonify({"success": True, "message": msg})
            
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Błąd podczas resetu: {e}"}), 500


# POST /api/admin/simulate - symulacja sezonu
@api_admin_bp.post("/api/admin/simulate")
@require_admin_api
def simulate_season():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"""
                SELECT status FROM {SCHEMA}.system_status 
                ORDER BY id DESC LIMIT 1
            """)
            status_row = cur.fetchone()
            if status_row and status_row[0] == 'SIMULATED':
                return jsonify({"error": "System jest już w stanie zasymulowanym. Najpierw wykonaj reset.", "warning": True}), 400
            
            cur.execute(f"SELECT * FROM {SCHEMA}.simulate_competitions()")
            results = cur.fetchall()
            
            if results:
                message = results[0][0] if results[0][0] else "Symulacja zakończona"
                events_processed = results[0][1] if len(results[0]) > 1 else 0
                results_created = results[0][2] if len(results[0]) > 2 else 0
                
                cur.execute(f"""
                    UPDATE {SCHEMA}.system_status 
                    SET status = 'SIMULATED', simulation_date = now(), updated_at = now()
                    WHERE id = (SELECT id FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1)
                """)
                conn.commit()
                
                msg = f"Symulacja zakończona! {message}. Przetworzono {events_processed} eventów, utworzono {results_created} wyników."
                return jsonify({"success": True, "message": msg})
            else:
                return jsonify({"error": "Symulacja nie zwróciła wyników. Sprawdź czy są aktywne eventy i rejestracje.", "warning": True}), 400
            
    except Exception as e:
        return jsonify({"error": f"Błąd podczas symulacji: {e}"}), 500

