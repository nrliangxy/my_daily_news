"""
启动方式(项目根目录, 指定cfg配置)：
celery -A backend.celery_task worker --loglevel=INFO
"""
import os

import time
import datetime
import json
from celery import Celery
from database import create_default_client
from backend.notify import Notification
# 动态使用
from health360 import *
import string

celery = Celery(__name__, broker=os.environ.get("CELERY_BROKER_URL", "redis://192.168.44.101:6379/5"))

task_notification = Notification(robot_url="https://oapi.dingtalk.com/robot/send?access_token=9f115406e358d84bb6b66c84c0e6371bfa5ca5258caf5e4cadb93a064b2cf713")


class QualityStatistics:
    def __init__(self, data_type, rule_name, export_directory, from_database="360_final"):
        mongo_client = create_default_client()
        self._rule_name = rule_name
        self._data_type = data_type
        self._rule = mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name})
        self._data_coll = mongo_client[from_database][data_type]
        self._report_coll = mongo_client["manager"]["quality_report"]
        self._rule_coll = mongo_client["manager"]["quality_rule"]
        self._rule_type = self._rule["rule_type"]
        before_locals = locals().copy()
        exec(self._rule["rule_content"])
        after_locals = locals().copy()
        for field in set(after_locals.keys()) - set(before_locals.keys()):
            globals().update({field: after_locals[field]})
        if self._rule_type == "function":
            self._functions = {func_name: after_locals["valid_" + func_name] for func_name in self._rule["rule_functions"]}
        else:
            rule_class = after_locals.get(self._rule["rule_class"])
            self._functions = {func_name: getattr(rule_class, "valid_" + func_name) for func_name in self._rule["rule_functions"]
                               if getattr(rule_class, "valid_" + func_name, None)}
        self._stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "field_stats": {field: {"success": 0, "failed": 0, "not_exists": 0, "sample": []}
                            for field in self._functions.keys()}
        }
        self.cost = 0
        self.export_file = os.path.join(export_directory, self._rule_name) + ".txt"

    def run(self):
        # project = {k: 1 for k in self._functions.keys()}
        with open(self.export_file, "w") as fout:
            start_time = time.time()
            for row in self._data_coll.find({}):
                valid_pass = self.valid_row(row)
                if not valid_pass:
                    export_row = {key: row[key] for key in self._rule["rule_functions"] if row.get(key)}
                    export_row.update({"_id": row["_id"]})
                    fout.write(json.dumps(export_row))
                    fout.write("\n")
            self.cost = time.time() - start_time
            self._report_coll.update_one({"rule_name": self._rule_name}, {"$set": {
                "cost_time": self.cost,
                "report": self._stats,
                "create_time": datetime.datetime.now(),
                "update_time": datetime.datetime.now(),
                "rule_name": self._rule_name}
            }, upsert=True)
        self.update_finish_status()

    def valid_row(self, row):
        self._stats["total"] += 1
        success_flag = True
        for field, vf in self._functions.items():
            self._stats["field_stats"].setdefault(field, {"success": 0, "failed": 0})
            if row.get(field) is None:
                self.not_exists_update(field, row)
                continue
            try:
                success = vf(**row)
            except Exception as e:
                print(e)
                self.failed_update(field, row)
                success_flag = False
                continue
            if success:
                self.success_update(field, row)
            else:
                success_flag = False
                self.failed_update(field, row)
        if success_flag:
            self._stats["success"] += 1
        else:
            self._stats["failed"] += 1
        return success_flag

    def failed_update(self, field, row):
        self._stats["field_stats"][field]["failed"] += 1
        if len(self._stats["field_stats"][field]["sample"]) < 1:
            self._stats["field_stats"][field]["sample"].append({row['_id']: row[field]})

    def success_update(self, field, row):
        self._stats["field_stats"][field]["success"] += 1

    def not_exists_update(self, field, row):
        self._stats["field_stats"][field]["not_exists"] += 1

    @property
    def stats(self):
        return self._stats

    def update_finish_status(self):
        self._rule_coll.update_one({
            "rule_name": self._rule_name,
        }, {"$set": {"status": "finish", "update_time": datetime.datetime.now()}})


@celery.task()
def data_quality_valid(data_type, rule_name, export_directory, from_database=None):
    q = QualityStatistics(data_type, rule_name, export_directory, from_database=from_database)
    try:
        q.run()
        msg = "success"
        task_notification.remind(f"规则: ->[飞吻][{rule_name}][跳舞] 已经处理完毕, 请在 http://192.168.44.101:5657/quality/index 上获取报告")
    except Exception as e:
        q.update_finish_status()
        msg = "%s" % e
        task_notification.remind(f"规则: ->[{rule_name}][捂脸哭] 处理失败,请跳转至http://192.168.44.101:5658/tasks 查看任务失败原因。")
    return msg


if __name__ == '__main__':
    data_quality_valid("organization", "的我去多1", r"D:\quality_report", from_database="360_etl")
    # q = QualityStatistics("organization", "的我去多1", r"D:\quality_report", from_database="360_final")
    # q.run()
    # print(q.stats)