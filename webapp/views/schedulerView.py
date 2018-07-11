from flask import Blueprint, render_template, request
from webapp.utils.tools import session_load
from webapp import bg_manager, stm_manager
from database.models import TaskLog, SchedulerTask

sche_bp = Blueprint("sche_view", __name__, url_prefix="/scheduler")


def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


@sche_bp.route('/index', methods=["GET", "POST"])
@session_load("scheduler")
def scheduler_index():
    tasks = bg_manager.list_task()
    return render_template("scheduler/index.html", bg_tasks=tasks)


@sche_bp.route('/scheduler_result', methods=["GET", "POST"])
@session_load("scheduler")
def scheduler_result():
    show_live_process()
    form_data = {k: v for k, v in request.form.items() if v is not None and len(v) > 0}
    if not form_data:
        records, info = check_db()
        return render_template("scheduler/result_page.html", info=info, records=records)
    command = form_data.get('command')
    name = form_data.get('name')
    db_task_name = show_task_name()
    if name in db_task_name:
        records, info = check_db(name)
        return render_template("scheduler/result_page.html", info=info, records=records)
    if command:
        command_list = command.split()
    else:
        return error_field_check_403("没有输入相关命令")
    stm_manager.start_command_process(name, command_list)
    
    try:
        show_live_process()
        records, info = check_db(name)
        return render_template("scheduler/result_page.html", info=info, records=records)
    except Exception as e:
        if "Tried to save duplicate unique keys" in str(e):
            return error_field_check_403("name is unique, your define name have existed")


@sche_bp.route('/scheduler_log', methods=["GET", "POST"])
@session_load("scheduler_f")
def scheduler_log():
    show_live_process()
    records, info = check_db()
    return render_template("scheduler/result_page.html", info=info, records=records)

def show_task_name():
    return [obj.task_name for obj in TaskLog.objects]


def show_live_process():
    stm_manager.show_live_process(TaskLog)
   


def check_db(name=None):
    records = [
        {"task_id": task.task_id, "task_name": task.task_name, "start_time": task.start_time, "status": task.status,
         "task_file_path": task.task_file_path, "pid_num": task.pid_num} for task in TaskLog.objects]
    if name:
        for i in records:
            if i['task_name'] == name:
                n = records.index(i)
                temp = records.pop(n)
                records.insert(0, temp)
    info = {
        "count": len(records) or 0,
        "other_field": "task_name",
        "status": "status"
    }
    return records, info
