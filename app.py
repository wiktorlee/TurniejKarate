import os
from flask import Flask, jsonify
from dotenv import load_dotenv
import psycopg

#Wczytanie dane z .env
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
DB_URL = os.getenv("DATABASE_URL")


@app.get("/")
def index():
    return "Flask działa poprawnie!"

#Test połączenia z Supabase
@app.get("/health/db")
def health_db():
    if not DB_URL:
        return jsonify(ok=False, error="Brak DATABASE_URL w .env"), 500
    try:
        with psycopg.connect(DB_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                return jsonify(ok=True, db_version=version)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True)
