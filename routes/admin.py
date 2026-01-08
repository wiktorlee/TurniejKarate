from flask import Blueprint, render_template, redirect, url_for, session, flash
from database import get_conn
from config import SCHEMA
from functools import wraps

admin_bp = Blueprint('admin', __name__)


def require_admin(f):
    """Dekorator sprawdzający uprawnienia administratora"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get("user_id")
        if not uid:
            flash("Musisz być zalogowany.", "error")
            return redirect(url_for("auth.login"))
        
        # Sprawdź czy użytkownik jest administratorem
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT is_admin FROM {SCHEMA}.users WHERE id = %s", (uid,))
            row = cur.fetchone()
            if not row or not row[0]:
                flash("Brak uprawnień administratora.", "error")
                return redirect(url_for("main.index"))
        
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.get("/admin")
@require_admin
def dashboard():
    """Panel główny administratora"""
    # Data loading moved to API/JS - this route only serves template
    return render_template("admin/dashboard.html")


@admin_bp.post("/admin/restore-dummy-athletes")
@require_admin
def restore_dummy_athletes():
    """Wywołuje procedurę SQL do masowej rejestracji kukiełek (moved to API)"""
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/admin/reset")
@require_admin
def reset_system():
    """Reset systemu (moved to API)"""
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/admin/simulate")
@require_admin
def simulate_season():
    """Symulacja przebiegu sezonu (moved to API)"""
    return redirect(url_for("admin.dashboard"))
