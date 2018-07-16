import pymongo
from mongoengine import *
from urllib.parse import quote_plus


def create_default_client(username="etl_user", password="etl360"):
    uri = "mongodb://%s:%s@%s" % (
        quote_plus(username), quote_plus(password), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)


def init_mongonengin_connect(username="etl_user",
                             password="etl360"):
    connect(
        authentication_source="admin",
        username=username,
        password=password,
        host='192.168.44.101',
        port=27100,
        db="manager"
    )