from flask import Blueprint, render_template

rankings_bp = Blueprint('rankings', __name__)


@rankings_bp.route("/rankings", methods=["GET"])
def show_rankings():
    # Data loading moved to API/JS - this route only serves template
    return render_template("rankings.html")
