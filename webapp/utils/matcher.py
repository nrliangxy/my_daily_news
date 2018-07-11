import re
import pymongo
from urllib.parse import quote_plus
import arrow


def create_default_client():
    uri = "mongodb://%s:%s@%s" % (
        quote_plus("root"), quote_plus("root360"), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)


class FieldMatcher:
    def __init__(self, field, other_field, client: pymongo.MongoClient, db, collection):
        self._field = field
        self._other_field = other_field
        self._client = client
        self._db_name = db
        self._db = self._client[self._db_name]
        self._collection_name = collection
        self._collection = self._db[self._collection_name]
        self._pipeline = []
        self._count = "match_count"

    def match_char_start(self, pattern):
        regex = re.compile("^[%s]" % re.escape(pattern))
        self._pipeline.append({
            "$match": {self._field: {"$regex": regex}}
        })
        return self

    def match_char_end(self, pattern):
        regex = re.compile("[%s]$" % re.escape(pattern))
        self._pipeline.append({
            "$match": {self._field: {"$regex": regex}}
        })
        return self

    def match_char(self, pattern):
        regex = re.compile("[%s]" % re.escape(pattern))
        self._pipeline.append({
            "$match": {self._field: {"$regex": regex}}
        })
        return self

    def match_word(self, word):
        regex = re.compile("%s" % re.escape(word))
        self._pipeline.append({
            "$match": {self._field: {"$regex": regex}}
        })
        return self

    def match_word_start(self, word):
        regex = re.compile("^%s" % re.escape(word))
        self._pipeline.append({
            "$match": {self._field: {"$regex": regex}}
        })
        return self

    def match_word_end(self, word):
        regex = re.compile("%s$" % re.escape(word))
        self._pipeline.append({
            "$match": {self._field: {"$regex": regex}}
        })
        return self

    def between_length(self, min_length=None, max_length=None):
        if self._other_field:
            self._pipeline.append({
                "$project": {
                    self._field: 1,
                    "length": {"$strLenCP": "$%s" % self._field},
                    self._other_field: 1}}
            )
        else:
            self._pipeline.append({
                "$project": {
                    self._field: 1,
                    "length": {"$strLenCP": "$%s" % self._field}}}
            )
        if min_length:
            self._pipeline.append({
                "$match": {"length": {"$gte": min_length}}
            })
        if max_length:
            self._pipeline.append({
                "$match": {"length": {"$lte": max_length}}
            })
        return self

    def count(self):
        pipeline = self.gen_pipeline()
        pipeline.append({"$count": self._count})
        for line in self._collection.aggregate(pipeline):
            return line[self._count]

    def apply(self, limit=10):
        pipeline = self.gen_pipeline(limit)
        return [r for r in self._collection.aggregate(pipeline)]

    def gen_pipeline(self, limit=None) -> list:
        pipeline = [
            {'$match': {"$and": [{self._field: {"$exists": True}}, {self._field: {"$ne": None}}]}}
        ]
        pipeline.extend(self._pipeline)
        if limit:
            pipeline.append({
                "$limit": limit
            })
        self._pipeline.append({
            "$project": {self._field: 1}
        })
        return pipeline

    def explain(self, limit=10):
        pipeline = self.gen_pipeline(limit)
        exp = self._db.command("aggregate", self._collection_name, pipeline=pipeline, explain=True)
        return exp['stages'][0]['$cursor']["query"]


class DateMatcher(FieldMatcher):
    def __init__(self, field, other_field, client: pymongo.MongoClient, db, collection):
        super().__init__(field, other_field, client, db, collection)
        if field.endswith("_ts"):
            self._field = field

    def _valid_method(self, date):
        if '-' not in date:
            if 57600 < int(date) < 4102502400:
                return date
        else:
            time = '-'.join([i if len(i) != 1 else '0' + str(i) for i in date.split('-')])
            return arrow.get(time).timestamp

    def between_date(self, min_date=None, max_date=None):
        if self._other_field:
            self._pipeline.append({
                "$project": {
                    self._field: 1,
                    self._other_field: 1
                }}
            )
        else:
            self._pipeline.append({
                "$project": {
                    self._field: 1,
                }}
            )
        if min_date:
            min_date = self._valid_method(min_date)
            self._pipeline.append(
                {"$match": {self._field: {"$gt": min_date}}
                 }
            )
        if max_date:
            max_date = self._valid_method(max_date)
            self._pipeline.append(
                {"$match": {self._field: {"$lte": max_date}}}
            )
        return self


def generate_date(field, other_field, client, db, collection, rule_data):
    date = DateMatcher(field, other_field, client, db, collection)
    if rule_data.get('mintime') or rule_data.get('maxtime'):
        date.between_date(rule_data.get('mintime'), rule_data.get('maxtime'))
    return date


def generate_matcher(field, other_field, client, db, collection, rule_data) -> FieldMatcher:
    m = FieldMatcher(field, other_field, client, db, collection)
    if rule_data.get("startswith"):
        m.match_char_start(rule_data["startswith"])
    if rule_data.get("endswith"):
        m.match_char_end(rule_data["endswith"])
    if rule_data.get("startword"):
        m.match_word_start(rule_data["startword"])
    if rule_data.get("endword"):
        m.match_word_end(rule_data["endword"])
    if rule_data.get("existsword"):
        m.match_word(rule_data["existsword"])
    if rule_data.get("minsize"):
        rule_data["minsize"] = int(rule_data["minsize"])
    if rule_data.get("maxsize"):
        rule_data["maxsize"] = int(rule_data["maxsize"])
    if rule_data.get("minsize") or rule_data.get("maxsize"):
        m.between_length(rule_data.get("minsize"), rule_data.get("maxsize"))
    return m


if __name__ == '__main__':
    f = FieldMatcher("title", None, create_default_client(), "360_rawdata", "funded_research")
    f.match_char_start("[0-9@#$%^&*+=?:;!|`]")
    print(f.count())
    print(f.apply(10))
