from flask import Blueprint, render_template, session
from webapp.utils.tools import session_load

index_bp = Blueprint("index_view", __name__)


@index_bp.route('/', methods=["GET", "POST"])
@index_bp.route('/index', methods=["GET", "POST"])
@session_load("index")
def index():
    print(session)
    return render_template("default/dashboard.html")


@index_bp.route('/index/<page>', methods=["GET", "POST"])
@session_load("index")
def display(page="index"):
    return render_template("default/%s.html" % page)