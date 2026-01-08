from flask import Blueprint, render_template, redirect, url_for, session, flash

auth_bp = Blueprint('auth', __name__)


#Rejestracja
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # POST handling moved to API - this route only serves template
    return render_template("register.html")


#Logowanie
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # POST handling moved to API - this route only serves template
    return render_template("login.html")


#Wylogowanie
@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Wylogowano.", "success")
    return redirect(url_for("auth.login"))

