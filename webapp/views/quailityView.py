from flask import Blueprint, render_template, request
from webapp.utils.matcher import FieldMatcher, create_default_client

quality_bp = Blueprint("quality_view", __name__, url_prefix="/quality")


def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


@quality_bp.route('/index', methods=["GET", "POST"])
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
def query():
    print(request.form)
    form_data = {k: v for k, v in request.form.items() if v is not None and len(v) > 0}

    db = request.form.get("db")
    if form_data.get("data_type") is None:
        return error_field_check_403("数据源未提供")
    data_type = form_data.pop("data_type")

    if form_data.get("field") is None:
        return error_field_check_403("查询字段未提供")
    field = form_data.pop("field")

    if len(form_data) == 0:
        return error_field_check_403("请至少提供一个查询条件")
    m = generate_matcher(field, create_default_client(), data_type, "nsf", form_data)

    records = m.apply(10)
    info = {
        "count": m.count() or 0,
        "query": m.explain(10),
        "field": field,
    }
    if info["count"] == 0:
        info.update({"msg": "反思一下为什么没结果！"})
    return render_template("quality/quality.html", info=info, limit=10,
                           records=records)


def generate_matcher(field, client, db, collection, rule_data) -> FieldMatcher:
    m = FieldMatcher(field, client, db, collection)
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