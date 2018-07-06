from flask import Blueprint, render_template, request
from webapp.utils.matcher import FieldMatcher, create_default_client, DateMatcher
from webapp.utils.tools import session_load

quality_bp = Blueprint("quality_view", __name__, url_prefix="/quality")


def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


@quality_bp.route('/index', methods=["GET", "POST"])
@session_load("quality")
def quality_index():
    data_type_list = [
        "fundedresearch",
        "grant",
        "news",
        "organization",
        "techofferring"
    ]
    return render_template("quality/index.html", data_source_list=data_type_list)


@quality_bp.route('/query', methods=["GET", "POST"])
@session_load("quality")
def query():
    print(request.form)
    print('='*77)
    form_data = {k: v for k, v in request.form.items() if v is not None and len(v) > 0}

    db = request.form.get("db")
    if form_data.get("data_type") is None:
        return error_field_check_403("数据源未提供")
    data_type = form_data.pop("data_type")

    if form_data.get("field") is None:
        return error_field_check_403("查询字段未提供")
    field = form_data.pop("field")
    other_field = form_data.pop("other_field") if form_data.get("other_field") else None
    if len(form_data) == 0:
        return error_field_check_403("请至少提供一个查询条件")
    print('-'*88)
    print(form_data)
    if form_data.get('mintime') or form_data.get('maxtime'):
        m = generate_date(field, other_field, create_default_client(), data_type, "nsf", form_data)
    else:
        m = generate_matcher(field, other_field, create_default_client(), data_type, "nsf", form_data)
    records = m.apply(10)
    print(records)
    info = {
        "count": m.count() or 0,
        "query": m.explain(10),
        "field": field,
        "other_field": other_field
    }
    return render_template("quality/quality.html", info=info, limit=10,
                           records=records)
def generate_date(field, other_field, client, db, collection, rule_data):
    date = DateMatcher(field, other_field, client, db, collection)
    if rule_data.get('mintime') or rule_data.get('maxtime'):
        date.between_date(rule_data.get('mintime'), rule_data.get('maxtime'))
    return date

def generate_matcher(field, other_field, client, db, collection, rule_data) -> FieldMatcher:
    m = FieldMatcher(field, other_field, client, db, collection)
    if rule_data.get("startswith"):
        m.match_char_start(rule_data["startswith"])
    if rule_data.get("endswith"):
        m.match_char_end(rule_data["endswith"])
    if rule_data.get("startword"):
        m.match_word_start(rule_data["startword"])
    if rule_data.get("endword"):
        m.match_word_end(rule_data["endword"])
    if rule_data.get("existsword"):
        m.match_word(rule_data["existsword"])
    if rule_data.get("minsize"):
        rule_data["minsize"] = int(rule_data["minsize"])
    if rule_data.get("maxsize"):
        rule_data["maxsize"] = int(rule_data["maxsize"])
    if rule_data.get("minsize") or rule_data.get("maxsize"):
        m.between_length(rule_data.get("minsize"), rule_data.get("maxsize"))
    return m
