from urllib.parse import quote
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from webapp import mongo_client
from webapp.utils.tools import session_load
from webapp.utils.code_analysis import CodeAnalyzer
from backend.celery_task import data_quality_valid
from webapp.utils.tools import to_timestamp, check_time
from collections import *
quality_bp = Blueprint("quality_view", __name__, url_prefix="/quality")


def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


@quality_bp.route('/index', methods=["GET", "POST"])
@session_load("quality")
def quality_index():
    collection_name = sorted(mongo_client["360_etl"].collection_names(), key=lambda x: x)
    return render_template("quality/index.html", data_source_list=collection_name)


@quality_bp.route('/query', methods=["GET", "POST"])
@session_load("quality")
def query():
    form_data = {k: v for k, v in request.form.items() if v is not None and len(v) > 0}
    if form_data.get("data_type") is None:
        return error_field_check_403("数据源未提供")
    data_type = form_data.pop("data_type")
    if form_data.get("rule_name") is None or len(form_data["rule_name"].strip()) <= 0:
        return error_field_check_403("规则名不合法")
    rule_name = form_data.get("rule_name")
    if form_data.get("rule_content") is None:
        return error_field_check_403("规则体未提供")
    from_database = form_data.get("database", "360_final")
    if from_database not in ["360_etl", "360_final"]:
        return error_field_check_403("非法数据库")
    print(request.form)
    rule_content = form_data.get("rule_content")
    operator = form_data.get("operator", "create")
    exist_rule = mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name})
    try:
        analysis_result = CodeAnalyzer(rule_content).get_analysis_result()
    except Exception as e:
        return error_field_check_403("规则代码分析失败, 错误描述：%s" % e)
    valid_functions = [func_name.split("_", 1)[-1] for func_name in analysis_result.get("functions", []) if
                       func_name.startswith("valid")]
    if len(valid_functions) <= 0:
        return error_field_check_403("不存在以valid开头的验证函数，请确保至少提交一个valid函数")
    if analysis_result.get("class"):
        rule_type = "class"
    else:
        rule_type = "function"
    # 创建操作时
    if operator == "create":
        if exist_rule:
            return error_field_check_403("无法创建，同名规则已存在！")
        else:
            row = mongo_client["manager"]["quality_rule"].insert_one({
                "rule_name": rule_name,
                "data_type": data_type,
                "rule_content": rule_content,
                "rule_type": rule_type,
                "rule_functions": valid_functions,
                "rule_class": analysis_result.get("class", None),
                "status": "running"
            })
            row_id = row.inserted_id
    elif operator == "update":
        if not exist_rule:
            return error_field_check_403("无法更新，不已存在该规则！")
        if exist_rule["status"] == "running":
            return error_field_check_403("无法更新，规则还在运行中，请稍后更新")
        else:
            mongo_client["manager"]["quality_rule"].update_one({
                "rule_name": rule_name
            }, {"$set": {"rule_content": rule_content,
                         "rule_type": rule_type,
                         "rule_functions": valid_functions,
                         "status": "running"}})
            row_id = exist_rule["_id"]
    else:
        return error_field_check_403("非法操作：%s" % operator)

    data_quality_valid.delay(data_type, rule_name, current_app.config['QUALITY_EXPORT_DIRECTORY'], from_database)

    return jsonify(result={
        "rule_name": rule_name,
        "data_type": data_type,
        "rule_type": rule_type,
        "rule_functions": valid_functions,
        "rule_class": analysis_result.get("class", None),
        "id": str(row_id)
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
        if mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name}):
            return error_field_check_403("规则%s正在运行中，请稍后查询" % rule_name)
        else:
            return error_field_check_403("规则%s运行中或不存在" % rule_name)
    return render_template("quality/report.html", reports=reports)


@quality_bp.route('/export/<rule_name>', methods=["GET", "POST"])
@session_load("quality")
def report_export(rule_name):
    directory = current_app.config["QUALITY_EXPORT_DIRECTORY"]
    try:
        filename = rule_name + ".txt"
        response = send_from_directory(directory=directory, filename=filename, as_attachment=True, cache_timeout=10)
        filename = filename.split(".")
        filename = quote(filename[0])
        response.headers["Content-Disposition"] = "attachment; filename={filename}.txt;".format(filename=filename)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers['Cache-Control'] = 'public, max-age=0'
    except Exception as e:
        return error_field_check_403("文件被删除，或不存在。请到文件所在目录%s查看" % directory)
    else:
        return response


@quality_bp.route("/health_check", methods=["GET", "POST"])
@session_load("quality")
def health_check():
    r = [
                {"$sort": {"data_status": 1}},
                {
                    "$group": {
                        "_id": "$data_status",
                        "count": {"$sum": 1},
                    }
                }
            ]
    time1 = request.form.get('data_time1')
    time2 = request.form.get('data_time2')
    if time1:
        # time1_stamp = to_timestamp(time1)
        r.insert(1, {"$match": {"updated_ts": {"$gte": time1}}})
    if time2:
        # time2_stamp = to_timestamp(time2)
        r.insert(1, {"$match": {"updated_ts": {"$lt": time2}}})
    
    data_type = request.form.get("data_type")
    data_type_list = mongo_client["360_etl"].collection_names()
    if data_type is None:
        return render_template("quality/health_check.html", data_type_list=data_type_list, data_type=None,
                               check_rows=[])
    if data_type not in data_type_list:
        return "data type is not exists"
    if request.method == "POST":
        try:
            check_rows = mongo_client["360_etl"][data_type].aggregate(r, allowDiskUse=True)
            print(r)
        except Exception as e:
            return jsonify(status=0, msg="查询失败")
        check_rows = [[row["count"], row["_id"]] for row in check_rows]
        return jsonify(status=1, check_rows=check_rows, total=sum([i[0] for i in check_rows]), data_type=data_type,
                       msg="success")
    else:
        return render_template("quality/health_check.html", data_type_list=data_type_list, data_type=None,
                               check_rows=[])


@quality_bp.route("/rule", methods=["GET", "POST"])
@session_load("quality")
def quality_rule():
    return ""
    # rule_name = request.form.get("quality-rule-name")
    # coll = mongo_client["manager"]["quality_rule"]
    # if rule_name is None or len(rule_name.strip()) == 0:
    #     reports = coll.find().sort([("create_time", -1)]).limit(1)
    # else:
    #     reports = coll.find({"rule_name": rule_name}).sort([("create_time", -1)]).limit(1)
    # reports = [i for i in reports]
    # if len(reports) <= 0:
    #     if mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name}):
    #         return error_field_check_403("规则%s正在运行中，请稍后查询" % rule_name)
    #     else:
    #         return error_field_check_403("规则%s运行中或不存在" % rule_name)
    # return render_template("quality/report.html", reports=reports)
