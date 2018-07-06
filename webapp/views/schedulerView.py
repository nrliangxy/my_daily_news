from flask import Blueprint, render_template
from webapp.utils.tools import session_load
from webapp import bg_manager

sche_bp = Blueprint("sche_view", __name__, url_prefix="/scheduler")


def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


@sche_bp.route('/index', methods=["GET", "POST"])
@session_load("scheduler")
def scheduler_index():
    tasks = bg_manager.list_task()
    return render_template("scheduler/index.html", bg_tasks=tasks)

