from flask import Blueprint, render_template, request
index_bp = Blueprint("index_view", __name__)


@index_bp.route('/', methods=["GET", "POST"])
@index_bp.route('/index', methods=["GET", "POST"])
def index():
    return render_template("default/dashboard.html")


@index_bp.route('/index/<page>', methods=["GET", "POST"])
def display(page="index"):
    return render_template("default/%s.html" % page)