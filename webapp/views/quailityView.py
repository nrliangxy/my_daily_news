from flask import Blueprint, render_template, request
from webapp.utils.matcher import FieldMatcher, create_default_client
quality_bp = Blueprint("quality_view", __name__, url_prefix="/quality")


@quality_bp.route('/query', methods=["GET", "POST"])
def query():
    db = request.form.get("db")
    table = request.form.get("table")
    field = request.form.get("field")
    rules = request.form.get("rule")
    m = FieldMatcher("title", create_default_client(), "fundedresearch", "cordis")
    m.match_char_start("hello")
    count = m.count()
    records = m.apply(10)
    q = m.explain(10)
    info = {
        "count": count,
        "query": q,
        "field": field or "title"
    }
    return render_template("quality/quality.html", info=info, limit=10,
                           records=records)
