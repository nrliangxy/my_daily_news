#!/usr/bin/env python
# -*- coding: utf-8 -*-

from backend.task import SchedulerTaskManager
import redis
from database.models import TaskLog
from database import create_default_client, init_mongonengin_connect
from backend.notify import Notification

from common.logger_handler import LogHandler

logger = LogHandler('backend_manager')

robot_api = "https://oapi.dingtalk.com/robot/send?access_token=9219c3463ad5a349650da5ecbe73ba2ffa5487ff36ad6cd8223ca668f305f9ee"

# 初始化mongo服务
init_mongonengin_connect()
mongo_client = create_default_client()
# 初始化后台任务
stm_manager = SchedulerTaskManager(mongo_client)
#redis
pool = redis.ConnectionPool(host='192.168.44.101', port=6379, decode_responses=True)
R = redis.Redis(connection_pool=pool)


def show_task_name():
    return {obj.task_name: obj for obj in TaskLog.objects}


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

temp = []
def start_command():
    try:
        while True:
            r = [i['task_name'] for i in check_db()[0] if i['status'] == 'stop']
            if r:
                r_2 = []
                for i in r:
                    if i not in set(temp):
                        r_2.append(i)
                if r_2:
                    n = Notification(robot_api)
                    temp.extend(r)
                    print(n.remind("%s have been hung up" % str(r_2)))
                    continue
            if R.lrange('form_data2', 0, -1):
                form_data = R.lpop('form_data2')
                if form_data != 1:
                    form_data = eval(form_data)
                    command = form_data.get('command')
                    command_list = command.split()
                    name = form_data.get('name')
                    db_task_name = show_task_name()
                    if name in db_task_name.keys():
                        obj = db_task_name[name]
                        pid = obj.pid_num
                        if stm_manager.check_pid(pid):
                            stm_manager.kill_process_by_pid(pid)
                        obj.delete()
                        show_live_process()
                        stm_manager.start_command_process(name, command_list)
                    else:
                        stm_manager.start_command_process(name, command_list)
    except Exception as e:
        logger.info(str(e))
        

        
        


if __name__ == '__main__':
    start_command()
