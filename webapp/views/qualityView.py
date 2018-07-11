from flask import Blueprint, render_template, request, jsonify
from webapp import mongo_client
from webapp.utils.tools import session_load
from webapp.utils.code_analysis import CodeAnalyzer
from database.schema import TABLE_SCHEMA
from backend.celery_task import data_quality_valid


quality_bp = Blueprint("quality_view", __name__, url_prefix="/quality")


def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


@quality_bp.route('/index', methods=["GET", "POST"])
@session_load("quality")
def quality_index():
    return render_template("quality/index.html", data_source_list=TABLE_SCHEMA.keys())


@quality_bp.route('/query', methods=["GET", "POST"])
@session_load("quality")
def query():
    form_data = {k: v for k, v in request.form.items() if v is not None and len(v) > 0}
    if form_data.get("data_type") is None:
        return error_field_check_403("数据源未提供")
    data_type = form_data.pop("data_type")
    if form_data.get("rule_name") is None and len(form_data["rule_name"].strip()) <= 0:
        return error_field_check_403("规则名不合法")
    rule_name = form_data.get("rule_name")
    if form_data.get("rule_content") is None:
        return error_field_check_403("规则体未提供")
    rule_content = form_data.get("rule_content")
    try:
        analysis_result = CodeAnalyzer(rule_content).get_analysis_result()
    except Exception as e:
        return error_field_check_403("规则代码分析失败, 错误描述：%s" % e)
    valid_functions = [func_name.split("_", 1)[-1] for func_name in analysis_result.get("functions", []) if func_name.startswith("valid")]
    if len(valid_functions) <= 0:
        return error_field_check_403("不存在以valid开头的验证函数，请确保至少提交一个valid函数")
    if analysis_result.get("class"):
        rule_type = "class"
    else:
        rule_type = "function"

    if mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name}):
        return error_field_check_403("同名规则已存在")
    row = mongo_client["manager"]["quality_rule"].insert_one({
        "rule_name": rule_name,
        "data_type": data_type,
        "rule_content": rule_content,
        "rule_type": rule_type,
        "rule_functions": valid_functions
    })

    data_quality_valid.delay(data_type, rule_name)
    return jsonify(result={
        "rule_name": rule_name,
        "data_type": data_type,
        "rule_type": rule_type,
        "rule_functions": valid_functions,
        "id": str(row.inserted_id)
    })


@quality_bp.route('/report', methods=["GET", "POST"])
@session_load("quality")
def quality_report():
    rule_name = request.form.get("quality-rule-name")
    coll = mongo_client["manager"]["quality_report"]
    if rule_name is None or len(rule_name.strip()) == 0:
        reports = coll.find().sort([("create_time", -1)]).limit(1)
    else:
        reports = coll.find({"rule_name": rule_name}).sort([("create_time", -1)]).limit(1)
    reports = [i for i in reports]
    if len(reports) <= 0:
        return error_field_check_403("规则%s运行中或不存在" % rule_name)
    return render_template("quality/report.html", reports=reports)



