from flask import Blueprint, render_template, redirect, url_for, session

profile_bp = Blueprint('profile', __name__)


#Profil
@profile_bp.get("/profile")
def profile():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    return render_template("profile.html")


#Edycja profilu
@profile_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    return render_template("edit_profile.html")

