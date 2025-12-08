from flask import Blueprint, redirect, url_for, session, jsonify
from database import get_conn
from config import DB_URL

main_bp = Blueprint('main', __name__)


@main_bp.get("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("profile.profile"))
    return redirect(url_for("auth.register"))


#Health check
@main_bp.get("/health/db")
def health_db():
    if not DB_URL:
        return jsonify(ok=False, error="Brak DATABASE_URL w .env"), 500
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
        return jsonify(ok=True, db_version=version)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

