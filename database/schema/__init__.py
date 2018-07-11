import json
import os


def _init():
    s = {}
    root_path = os.path.split(__file__)[0]
    for f in os.listdir(root_path):
        if not f.endswith(".json"):
            continue
        with open(os.path.join(root_path, f)) as fp:
            res = json.load(fp)
            fields = [i["name"] for i in res["fields"] if i["name"] not in ["sequence_number",
                                                                            "event_name",
                                                                            "health_error",
                                                                            ]]
            s.update({
                f.split(".")[0]: list(sorted(fields, key=lambda x: x))
            })
    return s


TABLE_SCHEMA = _init()
