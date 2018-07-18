#!/usr/bin/env python
# -*- coding: utf-8 -*-

from backend.task import SchedulerTaskManager
import redis, psutil
from uuid import uuid1
import pymongo
from database.models import TaskLog
from database.models import TaskLog
from urllib.parse import quote_plus
from database import create_default_client, init_mongonengin_connect

# def create_default_client(username="etl_user", password="etl360"):
#     uri = "mongodb://%s:%s@%s" % (
#         quote_plus(username), quote_plus(password), "192.168.44.101:27100")
#     return pymongo.MongoClient(uri)
# 初始化mongo服务
init_mongonengin_connect()
mongo_client = create_default_client()
# 初始化后台任务
stm_manager = SchedulerTaskManager(mongo_client)
r = redis.Redis(host='192.168.44.101', port=6379)

sub = r.pubsub()
sub.subscribe('form_data')


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


def start_command():
    while True:
        print('=' * 66)
        form_data = sub.parse_response()[-1]
        if form_data != 1:
            form_data = eval(form_data)
            name = form_data[0]
            command_list = form_data[1]
            show_live_process()
            stm_manager.start_command_process(name, command_list)
            show_live_process()


if __name__ == '__main__':
    start_command()
