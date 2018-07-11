import pymongo
import datetime
from mongoengine import *
from urllib.parse import quote_plus


def create_default_client():
    uri = "mongodb://%s:%s@%s" % (
        quote_plus("root"), quote_plus("root360"), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)

# connect(db="manager", host='mongodb://root:root360@192.168.44.101:27100', username="root", password='root360')
connect(
    authentication_source= "admin",
    username="root",
    password='root360',
    host='192.168.44.101',
    port=27100,
    db = "manager"
)
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
    task_name = StringField(required=True, unique=True)
    task_id = StringField(required=True)
    start_time = DateTimeField(default=datetime.datetime.now())
    # RUNNING、FINISH、ERROR
    status = StringField(required=True, default="RUNNING")
    pid_num = IntField(required=True)
    task_file_path = StringField(required=True)
    
    


