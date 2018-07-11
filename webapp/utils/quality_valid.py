from health360 import *

import time
import datetime
from webapp import mongo_client


class QualityStatistics:
    def __init__(self, data_type, rule_name):
        self._rule_name = rule_name
        self._data_type = data_type
        self._rule = mongo_client["manager"]["quality_rule"].find_one({"rule_name": rule_name})
        self._data_coll = mongo_client["360_rawdata"][data_type]
        self._report_coll = mongo_client["manager"]["quality_report"]

        exec(self._rule["rule_content"])
        local_vars = locals()
        self._functions = {func_name: local_vars["valid_" + func_name] for func_name in self._rule["rule_functions"]}
        self._stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "field_stats": {field: {"success": 0, "failed": 0, "not_exists": 0, "sample": []}
                            for field in self._functions.keys()}
        }
        self.cost = 0

    def run(self):
        # project = {k: 1 for k in self._functions.keys()}
        start_time = time.time()
        for row in self._data_coll.find({}).limit(1000):
            self.valid_row(row)
        self.cost = time.time() - start_time
        self._report_coll.insert_one({
            "cost_time": self.cost,
            "report": self._stats,
            "create_time": datetime.datetime.now(),
            "rule_name": self._rule_name
        })

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
                self.failed_update(field, row)
                success_flag = False
                continue
            if success:
                self.success_update(field, row)
            else:
                success_flag = True
                self.failed_update(field, row)
        if success_flag:
            self._stats["success"] += 1
        else:
            self._stats["failed"] += 1

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


if __name__ == '__main__':
    q = QualityStatistics("funded_research", "fr验证")
    q.run()
    print(q.stats)



