from flask import Flask
from config import SECRET_KEY
from routes.main import main_bp
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.categories import categories_bp
from routes.registration import registration_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

#Rejestracja blueprintów
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(registration_bp)



if __name__ == "__main__":
    app.run(debug=True)
