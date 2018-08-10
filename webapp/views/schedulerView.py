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


def check_process(category):
    info = {"count": 10, "title": 'title', "date": "date"}
    coll = mongo_client['spider-file']['china_news']
    start_time_list = coll.find({'category': category}).sort("created_ts", -1).limit(10)
    process_records = [chang_r(i) for i in start_time_list]
    return info, process_records


@sche_bp.route('/china', methods=["GET", "POST"])
@session_load("china_news")
def scheduler_log_upload_process():
    # info = {"count": 10, "title": 'title', "date": "date"}
    # coll = mongo_client['spider-file']['china_news']
    # start_time_list = coll.find().sort("created_ts", -1).limit(10)
    # process_records = [chang_r(i) for i in start_time_list]
    info, process_records = check_process("china")
    info.update(dict(scheme="China news"))
    raw_data = [i['raw_data'] for i in process_records]
    return render_template("scheduler/result_page2.html", info=info, records=raw_data)


@sche_bp.route('/internationalbusiness', methods=["GET", "POST"])
@session_load("internationalbusiness_news")
def scheduler_log_dump_process():
    info, process_records = check_process("internationalbusiness")
    info.update(dict(scheme="International news"))
    raw_data = [i['raw_data'] for i in process_records]
    return render_template("scheduler/result_page2.html", info=info, records=raw_data)


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
    item['start_ts'] = timestamp_datetime(item['created_ts'])
    # item['end_ts'] = timestamp_datetime(item['end_ts'])
    return item


def check_db():
    records = [i for i in database.find()]
    # for i in records:
    #     database.update({'task_name': i['task_name']}, {'$set': {'status': i['status']}})
    # database.remove()
    # database.insert_many(records)
    # records = [
    #     {"task_id": task.task_id, "task_name": task.task_name, "start_time": task.start_time, "status": task.status,
    #      "task_file_path": task.task_file_path, "pid_num": task.pid_num} for task in TaskLog.objects]
    # if name:
    #     for i in records:
    #         if i['task_name'] == name:
    #             n = records.index(i)
    #             temp = records.pop(n)
    #             records.insert(0, temp)
    info = {
        "count": len(records) or 0,
        "other_field": "title",
        "status": "source_url"
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
        print('=' * 77)
        
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
