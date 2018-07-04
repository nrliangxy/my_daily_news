import re
import pymongo
from urllib.parse import quote_plus


def create_default_client():
    uri = "mongodb://%s:%s@%s" % (
        quote_plus("root"), quote_plus("root360"), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)


class FieldMatcher:
    def __init__(self, field, client: pymongo.MongoClient, db, collection):
        self._field = field
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
        self._pipeline.append({
            "$project": {self._field: 1,
                         "length": {"$strLenCP": "$%s" % self._field}}
        })
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
        print(pipeline)
        for line in self._collection.aggregate(pipeline):
            return line[self._count]

    def apply(self, limit=10):
        pipeline = self.gen_pipeline(limit)
        print(pipeline)
        return [r for r in self._collection.aggregate(pipeline)]

    def gen_pipeline(self, limit=None) -> list:
        pipeline = []
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


if __name__ == '__main__':
    m = FieldMatcher("title", create_default_client(), "fundedresearch", "nsf")
    m.between_length(10)
    count = m.count()
    records = m.apply(10)
    print(records)