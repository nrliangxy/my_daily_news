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
            "field_stats": {field: {"success": 0, "failed": 0, "sample": []} for field in self._functions.keys()}
        }
        self.cost = 0

    def run(self):
        # project = {k: 1 for k in self._functions.keys()}
        start_time = time.time()
        for row in self._data_coll.find({}):
            self.valid_row(row)
        self.cost = time.time() - start_time
        self._report_coll.insert_one({
            "cost_time": self.cost,
            "report": self._stats,
            "create_time": datetime.datetime.now(),
            "rule_name": self._rule_name
        })

    def valid_row(self, row):
        for field, vf in self._functions.items():
            self._stats["field_stats"].setdefault(field, {"success": 0, "failed": 0})
            self._stats["total"] += 1
            success = vf(**row)
            if success:
                self._stats["success"] += 1
                self._stats["field_stats"][field]["success"] += 1
            else:
                self._stats["failed"] += 1
                self._stats["field_stats"][field]["failed"] += 1
                if len(self._stats["field_stats"][field]["sample"]) <= 5:
                    self._stats["field_stats"][field]["sample"].append(row[field])

    @property
    def stats(self):
        return self._stats


if __name__ == '__main__':
    q = QualityStatistics("funded_research", "fundedresearch测试2")
    q.run()
    print(q.stats)



