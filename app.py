from flask import Flask
from config import SECRET_KEY
from routes.main import main_bp
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.categories import categories_bp
from routes.registration import registration_bp
from routes.rankings import rankings_bp
from routes.admin import admin_bp
from utils import get_system_status

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

#Rejestracja blueprintów
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(registration_bp)
app.register_blueprint(rankings_bp)
app.register_blueprint(admin_bp)

# Context processor - dostępność system_status we wszystkich szablonach
@app.context_processor
def inject_system_status():
    return dict(system_status=get_system_status())



if __name__ == "__main__":
    app.run(debug=True)
