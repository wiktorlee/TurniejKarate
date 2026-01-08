from flask import Blueprint, render_template, redirect, url_for, session

registration_bp = Blueprint('registration', __name__)


#Moje zgłoszenie
@registration_bp.get("/my-registration")
def my_registration():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    # Data loading moved to API/JS - this route only serves template
    return render_template("my_registration.html")


#Wycofanie całego zgłoszenia (moved to API)
@registration_bp.post("/withdraw")
def withdraw():
    # POST handling moved to API - redirect to my-registration
    return redirect(url_for("registration.my_registration"))


#Wycofanie pojedynczej dyscypliny (moved to API)
@registration_bp.post("/withdraw-discipline")
def withdraw_discipline():
    # POST handling moved to API - redirect to my-registration
    return redirect(url_for("registration.my_registration"))


#Lista zawodników Kata
@registration_bp.get("/kata/competitors/<int:event_id>/<int:category_kata_id>")
def kata_competitors(event_id, category_kata_id):
    """Wyświetla listę zawodników zapisanych do kategorii Kata."""
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    # Data loading moved to API/JS - this route only serves template
    return render_template("kata_competitors.html")


#Drzewko walk Kumite
@registration_bp.get("/kumite/bracket/<int:event_id>/<int:category_kumite_id>")
def kumite_bracket(event_id, category_kumite_id):
    """Wyświetla drzewko walk dla kategorii Kumite."""
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    # Data loading moved to API/JS - this route only serves template
    return render_template("kumite_bracket.html")
