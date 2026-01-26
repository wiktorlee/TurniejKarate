from flask import Blueprint, render_template

rankings_bp = Blueprint('rankings', __name__)


@rankings_bp.route("/rankings", methods=["GET"])
def show_rankings():
    return render_template("rankings.html")
