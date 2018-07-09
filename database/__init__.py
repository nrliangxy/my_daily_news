import pymongo
import datetime
from mongoengine import *
from urllib.parse import quote_plus


def create_default_client():
    uri = "mongodb://%s:%s@%s" % (
        quote_plus("root"), quote_plus("root360"), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)


class SchedulerTask(Document):
    """
    任务类型：
        定时任务
        非定时任务
    """
    task_name = StringField(required=True, max_length=200)
    task_type = StringField(required=True)
    task_command = StringField()
    task_trigger = StringField()
    create_time = DateTimeField(default=datetime.datetime.utcnow())


class TaskLog(Document):
    task_id = StringField(required=True)
    start_time = DateTimeField(default=datetime.datetime.utcnow())
    # RUNNING、FINISH、ERROR
    status = StringField(required=True, default="RUNNING")
