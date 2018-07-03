import re
import pymongo
from urllib.parse import quote_plus


def create_default_client():
    uri = "mongodb://%s:%s@%s" % (
        quote_plus("root"), quote_plus("root360"), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)


class MongoRule:
    def __init__(self, client):
        self._client = client
        self._pipeline = []


#
# def pattern_translate(pattern_str, ):
#     return {"$regex": re.compile()}


if __name__ == '__main__':
    m = MongoRule(create_default_client())

