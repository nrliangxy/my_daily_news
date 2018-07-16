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
# 动态使用
from health360 import *
import string

celery = Celery(__name__, broker=os.environ.get("CELERY_BROKER_URL", "redis://192.168.44.101:6379/5"))


class QualityStatistics:
    def __init__(self, data_type, rule_name, export_directory):
        mongo_client = create_default_client()
        self._rule_name = rule_name
        self._data_type = data_type
        self._rule = mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name})
        self._data_coll = mongo_client["360_etl"][data_type]
        self._report_coll = mongo_client["manager"]["quality_report"]
        self._rule_coll = mongo_client["manager"]["quality_rule"]
        self._rule_type = self._rule["rule_type"]
        exec(self._rule["rule_content"])
        local_vars = locals()
        if self._rule_type == "function":
            self._functions = {func_name: local_vars["valid_" + func_name] for func_name in self._rule["rule_functions"]}
        else:
            rule_class = local_vars.get(self._rule["rule_class"])
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
        self._rule_coll.update_one({
            "rule_name": self._rule_name,
}, {"$set": {"status": "finish", "update_time": datetime.datetime.now()}})

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
            self._stats["field_stats"][field]["sample"].append({row['repo_id']: row[field]})

    def success_update(self, field, row):
        self._stats["field_stats"][field]["success"] += 1

    def not_exists_update(self, field, row):
        self._stats["field_stats"][field]["not_exists"] += 1

    @property
    def stats(self):
        return self._stats


@celery.task()
def data_quality_valid(data_type, rule_name, export_directory):
    try:
        q = QualityStatistics(data_type, rule_name, export_directory)
        q.run()
        print("finish %s valid" % rule_name)
    except Exception as e:
        return "%s" % e
    return "success"


if __name__ == '__main__':
    q = QualityStatistics("funded_research", "full_valid", r"D:\quality_report")
    q.run()
    print(q.stats)