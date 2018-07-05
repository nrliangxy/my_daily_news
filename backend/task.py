import pymongo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from enum import Enum, unique


@unique
class TaskStatus(Enum):
    STOP = "stop"
    RUNNING = "running"


class BackgroundTaskManager:
    """
    #: constant indicating a scheduler's stopped state
    STATE_STOPPED = 0
    #: constant indicating a scheduler's running state (started and processing jobs)
    STATE_RUNNING = 1
    #: constant indicating a scheduler's paused state (started but not processing jobs)
    STATE_PAUSED = 2
    """
    def __init__(self, database: pymongo.MongoClient):
        self._scheduler = BackgroundScheduler()
        self._coll = database["manager"]["scheduler"]

    def start(self):
        assert self._scheduler.state != 1
        self._coll.update_many({}, {"$set": {"status": TaskStatus.STOP.value}})
        self._scheduler.start()

    def shutdown(self):
        self._scheduler.shutdown()

    def start_interval_job(self, func, trigger, name, kwargs=None, replace_existing=True):
        assert self._scheduler.state == 1
        record = self._coll.find_one({"name": name})
        if not record:
            record_id = self._coll.insert_one({
                "name": name,
                "trigger": trigger,
            }).inserted_id
        else:
            record_id = record["_id"]
        self._scheduler.add_job(func=func,
                                trigger=IntervalTrigger(**trigger),
                                id=str(record_id),
                                kwargs=kwargs,
                                name=name,
                                replace_existing=replace_existing)

    def stop_interval_job(self, name):
        record = self._coll.find_one({"name": name})
        if record:
            try:
                self._scheduler.remove_job(str(record["_id"]))
            except JobLookupError as e:
                pass
            self._coll.update({"_id": record["_id"]}, {"$set": {"status": TaskStatus.STOP.value}})

    def list_task(self, state=None) -> list:
        """获取当前所有的定时任务"""
        result = []
        if state is None:
            tasks = self._coll.find({})
        else:
            tasks = self._coll.find({"state": state})
        for task in tasks:
            try:
                job = self._scheduler.get_job(job_id=str(task["_id"]))
            except:
                job = None
            result.append({
                "id": str(task["_id"]),
                "name": task["name"],
                "trigger": task["trigger"],
                "status": task["status"],
                "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job else None
            })
        print(result)
        return result

