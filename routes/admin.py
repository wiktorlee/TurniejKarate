from flask import Blueprint, render_template, redirect, url_for, session, flash, request
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
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Pobierz status systemu
            cur.execute(f"""
                SELECT status, simulation_date, reset_date, updated_at
                FROM {SCHEMA}.system_status 
                ORDER BY id DESC LIMIT 1
            """)
            status_row = cur.fetchone()
            
            # Pobierz statystyki
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
                "simulation_date": status_row[1] if status_row else None,
                "reset_date": status_row[2] if status_row else None,
                "updated_at": status_row[3] if status_row else None
            }
            
            return render_template("admin/dashboard.html",
                                 system_status=system_status,
                                 dummy_count=dummy_count,
                                 active_events=active_events,
                                 results_count=results_count,
                                 registrations_count=registrations_count)
    except Exception as e:
        flash(f"Błąd podczas ładowania panelu: {e}", "error")
        return redirect(url_for("main.index"))


@admin_bp.post("/admin/restore-dummy-athletes")
@require_admin
def restore_dummy_athletes():
    """Wywołuje procedurę SQL do masowej rejestracji kukiełek"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Wywołaj procedurę SQL
            cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
            results = cur.fetchall()
            
            # Oblicz statystyki
            total_registrations = sum(row[2] for row in results if isinstance(row[2], int)) if results else 0
            athletes_processed = len([r for r in results if r[2] and r[2] > 0]) if results else 0
            
            if total_registrations > 0:
                flash(
                    f"Pomyślnie zarejestrowano {total_registrations} zapisów dla {athletes_processed} kukiełek.", 
                    "success"
                )
            else:
                # Sprawdź czy to brak kukiełek czy wszystkie już zarejestrowane
                if results and results[0][0] == 'Brak kukiełek do zarejestrowania':
                    flash(
                        "Brak kukiełek do zarejestrowania. Upewnij się, że istnieją użytkownicy z is_dummy=true i przypisanymi kategoriami.", 
                        "info"
                    )
                else:
                    flash(
                        "Brak nowych rejestracji do utworzenia. (Wszystkie kukiełki mogą być już zarejestrowane lub brak aktywnych eventów)", 
                        "info"
                    )
            
            return redirect(url_for("admin.dashboard"))
            
    except Exception as e:
        flash(f"Błąd podczas rejestracji kukiełek: {e}", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.post("/admin/reset")
@require_admin
def reset_system():
    """Reset systemu - usuwa wyniki i drzewka, opcjonalnie przywraca rejestracje kukiełek"""
    restore_dummies = request.form.get("restore_dummies") == "true"
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            conn.execute("BEGIN")
            
            # 1. Usuń wyniki
            cur.execute(f"DELETE FROM {SCHEMA}.results")
            deleted_results = cur.rowcount
            
            # 2. Usuń drzewka walk
            cur.execute(f"DELETE FROM {SCHEMA}.draw_fight")
            deleted_fights = cur.rowcount
            
            # 3. Opcjonalnie: przywróć rejestracje kukiełek
            restored_count = 0
            if restore_dummies:
                cur.execute(f"SELECT * FROM {SCHEMA}.restore_dummy_athletes_registrations()")
                results = cur.fetchall()
                restored_count = sum(row[2] for row in results if isinstance(row[2], int)) if results else 0
            
            # 4. Zaktualizuj status systemu
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
            flash(msg, "success")
            
            return redirect(url_for("admin.dashboard"))
            
    except Exception as e:
        conn.rollback()
        flash(f"Błąd podczas resetu: {e}", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.post("/admin/simulate")
@require_admin
def simulate_season():
    """Symulacja przebiegu sezonu - generuje losowe wyniki dla wszystkich zarejestrowanych zawodników"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Sprawdź czy system nie jest już zasymulowany
            cur.execute(f"""
                SELECT status FROM {SCHEMA}.system_status 
                ORDER BY id DESC LIMIT 1
            """)
            status_row = cur.fetchone()
            if status_row and status_row[0] == 'SIMULATED':
                flash("System jest już w stanie zasymulowanym. Najpierw wykonaj reset.", "warning")
                return redirect(url_for("admin.dashboard"))
            
            # Wywołaj procedurę SQL symulacji
            cur.execute(f"SELECT * FROM {SCHEMA}.simulate_competitions()")
            results = cur.fetchall()
            
            if results:
                message = results[0][0] if results[0][0] else "Symulacja zakończona"
                events_processed = results[0][1] if len(results[0]) > 1 else 0
                results_created = results[0][2] if len(results[0]) > 2 else 0
                
                # Zaktualizuj status systemu na SIMULATED
                cur.execute(f"""
                    UPDATE {SCHEMA}.system_status 
                    SET status = 'SIMULATED', simulation_date = now(), updated_at = now()
                    WHERE id = (SELECT id FROM {SCHEMA}.system_status ORDER BY id DESC LIMIT 1)
                """)
                conn.commit()
                
                flash(
                    f"Symulacja zakończona! {message}. Przetworzono {events_processed} eventów, utworzono {results_created} wyników.",
                    "success"
                )
            else:
                flash("Symulacja nie zwróciła wyników. Sprawdź czy są aktywne eventy i rejestracje.", "warning")
            
            return redirect(url_for("admin.dashboard"))
            
    except Exception as e:
        flash(f"Błąd podczas symulacji: {e}", "error")
        return redirect(url_for("admin.dashboard"))




