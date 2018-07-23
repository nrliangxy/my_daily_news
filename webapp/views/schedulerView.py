from flask import Blueprint, render_template, request
from webapp.utils.tools import session_load
from webapp import bg_manager, stm_manager, mongo_client
from database.models import TaskLog
import time
import redis, os
from database import create_default_client
import psutil
from psutil import STATUS_ZOMBIE
from collections import namedtuple
import redis
pool = redis.ConnectionPool(host='192.168.44.101', port=6379, decode_responses=True)
# r = redis.Redis(host='192.168.44.101', port=6379)

r = redis.Redis(connection_pool=pool)
# r = redis.Redis(host='192.168.44.101', port=6379)
sche_bp = Blueprint("sche_view", __name__, url_prefix="/scheduler")
D = create_default_client()
database = D['manager']['task_log']


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
    if form_data:
        r.lpush("form_data2", form_data)
        # r.publish('form_data', form_data)
        name = form_data.get('name')
        records, info = check_db(name)
        return render_template("scheduler/result_page.html", info=info, records=records)
       

@sche_bp.route('/scheduler_log', methods=["GET", "POST"])
@session_load("scheduler_f")
def scheduler_log():
    records, info = check_db()
    return render_template("scheduler/result_page.html", info=info, records=records)

    
def check_pid(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def check_records(items):
    for i in items:
        p_num = i['pid_num']
        if check_pid(p_num):
            p = psutil.Process(p_num)
            if p.status() == STATUS_ZOMBIE:
                SmallTask.kill_process_by_pid(p_num)
                i['status'] = 'stop'
            else:
                i['status'] = 'RUNNING'
        else:
            i['status'] = 'stop'
    return items


@sche_bp.route('/scheduler_log_upload_process', methods=["GET", "POST"])
@session_load("scheduler_f_process")
def scheduler_log_upload_process():
    info = {"count": 5}
    coll = mongo_client['manager']['fetch_task']
    start_time_list = coll.find().sort("start_ts", -1).limit(5)
    process_records = [chang_r(i) for i in start_time_list]
    return render_template("scheduler/result_page2.html", info=info, records=process_records)


@sche_bp.route('/scheduler_log_dump_process', methods=["GET", "POST"])
@session_load("scheduler_f_process")
def scheduler_log_dump_process():
    info = {"count": 5}
    coll = mongo_client['360_rawdata']['sync_log']
    start_time_list = coll.find().sort("created_time", -1).limit(5)
    start_time_list = [i for i in start_time_list]
    return render_template("scheduler/result_page3.html", info=info, records=start_time_list)


def show_task_name():
    return {obj.task_name: obj for obj in TaskLog.objects}


def show_live_process():
    stm_manager.show_live_process(TaskLog)


def timestamp_datetime(value):
    format = '%Y-%m-%d %H:%M:%S'
    # value为传入的值为时间戳(整形)，如：1332888820
    value = time.localtime(value)
    dt = time.strftime(format, value)
    return dt


def chang_r(item):
    item['start_ts'] = timestamp_datetime(item['start_ts'])
    item['end_ts'] = timestamp_datetime(item['end_ts'])
    return item






def check_db(name=None):
    records = [i for i in database.find()]
    records = check_records(records)
    for i in records:
        database.update({'task_name': i['task_name']}, {'$set': {'status': i['status']}})
    # database.remove()
    # database.insert_many(records)
    # records = [
    #     {"task_id": task.task_id, "task_name": task.task_name, "start_time": task.start_time, "status": task.status,
    #      "task_file_path": task.task_file_path, "pid_num": task.pid_num} for task in TaskLog.objects]
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


class SmallTask(object):
    
    @classmethod
    def kill_process_by_pid(cls, pid):
        while True:
            try:
                cls.reap_children([pid])
            except Exception:
                continue
            else:
                break
                
    @classmethod
    def reap_children(cls, children_pid: list, timeout=3):
        """Tries hard to terminate and ultimately kill all the children of this process."""
        msg = "failed"
        print(children_pid)
        print('='*77)
        
        def on_terminate(proc):
            msg = "process {} terminated with exit code {}".format(proc, proc.returncode)
            return msg
        
        procs = psutil.Process().children()
        # send SIGTERM
        for p in procs:
            if p.pid in children_pid:
                p.terminate()
        gone, alive = psutil.wait_procs(procs, timeout=timeout, callback=on_terminate)
        if alive:
            # send SIGKILL
            for p in alive:
                if p.pid in children_pid:
                    msg = "process {} survived SIGTERM; trying SIGKILL" % p
                    print("process {} survived SIGTERM; trying SIGKILL" % p)
                    p.kill()
            gone, alive = psutil.wait_procs(alive, timeout=timeout, callback=on_terminate)
            if alive:
                # give up
                for p in alive:
                    if p.pid in children_pid:
                        msg = "process {} survived SIGKILL; giving up" % p
                        print("process {} survived SIGKILL; giving up" % p)
        return msg
