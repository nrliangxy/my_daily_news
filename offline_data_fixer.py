import pymongo
import json
import click
from urllib.parse import quote_plus


def create_default_client(username="etl_user", password="etl360"):
    uri = "mongodb://%s:%s@%s" % (
        quote_plus(username), quote_plus(password), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)


class Fixer:
    name = "fixer"

    def __init__(self, output=None, project_fields=None):
        self.projection = {field: 1 for field in project_fields}
        self.client = create_default_client()
        self.output = output
        self.f = open(output or (self.name + ".txt"), "w")
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()

    def rule_apply(self, row):
        raise NotImplemented

    def data_iter(self):
        raise NotImplemented

    def run(self):
        for row in self.data_iter():
            self.stats["total"] += 1
            if self.stats["total"] % 10000 == 0:
                print(self.stats)
            result = self.rule_apply(row)
            if result:
                self.stats["success"] += 1
                self.f.write(json.dumps(row))
                self.f.write("\n")
            else:
                self.stats["failed"] += 1
        print(self.stats)


class FundedOrgFixer(Fixer):
    def __init__(self):
        super().__init__(project_fields=["normalized_organization"])

    def data_iter(self):
        return self.client["360_etl"]["funded_research"].find({"$and": [{"normalized_organization": {"$exists": 1}},
                                                                        {"data_status": {"$eq": "ACTIVE"}}
                                                                        ]},
                                                              self.projection or {})

    def rule_apply(self, row):
        org_coll = self.client["360_etl"]["organization"]
        normalized_organization = row.pop("normalized_organization")
        old_size = len(normalized_organization)
        row["normalized_organization"] = []
        for org in normalized_organization:
            entity = org_coll.find_one({"_id": org["entity_id"]}, {"data_status": 1})
            if entity["data_status"] == "ACTIVE" and len(org["name"]) > 1:
                row["normalized_organization"].append(org)
        new_size = len(row["normalized_organization"])
        if len(row["normalized_organization"]) > 0 and old_size != new_size:
            return row
        return


@click.command()
@click.option("--processor", type=str, help="processor type")
@click.option("--output", type=str, help="output file")
def main(processor, output):
    processor_cls_str = "".join([i.title() for i in processor.split("_")]) + "Worker"
    processor_cls = globals()[processor_cls_str]
    with processor_cls(output):
        pass


if __name__ == '__main__':
    with FundedOrgFixer():
        pass
