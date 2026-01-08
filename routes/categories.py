from flask import Blueprint, render_template, redirect, url_for, session

categories_bp = Blueprint('categories', __name__)


#Kategorie
@categories_bp.route("/categories", methods=["GET", "POST"])
def categories():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("auth.login"))
    # Data loading and POST handling moved to API/JS - this route only serves template
    return render_template("categories.html")
