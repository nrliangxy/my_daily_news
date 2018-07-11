import datetime
from mongoengine import *


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


class QualityRule(Document):
    meta = {
        'collection': 'quality_rule'
    }
    rule_name = StringField(required=True, unique=True)
    data_type = StringField(required=True)
    rule_content = StringField(required=True)
    rule_type = StringField(required=True)
    rule_functions = ListField(required=True)


class QualityReport(Document):
    meta = {
        'collection': 'quality_report'
    }
    cost_time = FloatField(required=True)
    report = DictField()
    create_time = DateTimeField()
    rule_name = StringField()

