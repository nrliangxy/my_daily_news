import psutil
import os
import pymongo
from uuid import uuid1
from psutil import STATUS_ZOMBIE
from database.models import TaskLog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from enum import Enum, unique
from database.models import TaskLog


# from common.logger_handler import LogHandler

# logger = LogHandler('spider_shceduler')


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
        self._coll = database["manager"]["background"]
    
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


class SchedulerTaskManager:
    def __init__(self, database: pymongo.MongoClient):
        self._database = database['manager']['command']
        self._scheduled_task = self._check_pid()
    
    def _check_pid(self):
        pids = {}
        for task in TaskLog.objects:
            if self.check_pid(task.pid_num):
                obj = psutil.Process(task.pid_num)
                task.update(status="RUNNING")
                pids.update({task.task_name: obj})
        return pids
    
    def check_pid(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
    
    def start_command_process(self, command_id, command):
        command = ['nohup'] + command
        process = psutil.Popen(command)
        r_insert = {"task_id": str(uuid1()), "task_name": command_id, "pid_num": process.pid,
                    "task_file_path": command[2]}
        obj = TaskLog(**r_insert)
        obj.save()
        self._scheduled_task.setdefault(command_id, process)
        return command_id, process
    
    def kill_process_by_pid(self, pid):
        while True:
            try:
                self.reap_children([pid])
            except Exception:
                continue
            else:
                break
    
    def kill_process_by_name(self, process_name):
        """杀指定名称的进程"""
        p = self._scheduled_task.pop(process_name)
        while True:
            try:
                self.reap_children([p["pid"]])
            except Exception:
                continue
            else:
                break
    
    @classmethod
    def find_procs_by_name(cls, name):
        ls = []
        for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
            if name == p.info['name'] or \
                            p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                            p.info['cmdline'] and p.info['cmdline'][0] == name:
                ls.append(p)
        return ls
    
    @staticmethod
    def reap_children(children_pid: list, timeout=3):
        """Tries hard to terminate and ultimately kill all the children of this process."""
        msg = "failed"
        
        def on_terminate(proc):
            msg = "process {} terminated with exit code {}".format(proc, proc.returncode)
            return msg
        
        procs = psutil.Process().children()
        # send SIGTERM
        for p in procs:
            if p.pid in children_pid:
                p.terminate()
        gone, alive = psutil.wait_procs(procs, timeout=timeout, callback=on_terminate)
        if alive:
            # send SIGKILL
            for p in alive:
                if p.pid in children_pid:
                    msg = "process {} survived SIGTERM; trying SIGKILL" % p
                    print("process {} survived SIGTERM; trying SIGKILL" % p)
                    p.kill()
            gone, alive = psutil.wait_procs(alive, timeout=timeout, callback=on_terminate)
            if alive:
                # give up
                for p in alive:
                    if p.pid in children_pid:
                        msg = "process {} survived SIGKILL; giving up" % p
                        print("process {} survived SIGKILL; giving up" % p)
        return msg
    
    def refresh_process(self):
        zombies = []
        # print(self._scheduled_task)
        for pn, process in self._scheduled_task.items():
            # print(process.status())
            if process.status() == STATUS_ZOMBIE:
                zombies.append(pn)
                self.kill_process_by_pid(process.pid)
        for command_id in zombies:
            self._scheduled_task.pop(command_id)
        return self._scheduled_task
    
    def show_live_process(self, db_obj):
        live_process = self.refresh_process()
        live_list = list(live_process.keys())
        for obj in db_obj.objects:
            if obj.task_name not in live_list:
                obj.update(status='stop')
            


if __name__ == '__main__':
    import pymongo
    from urllib.parse import quote_plus
    
    
    def create_default_client():
        uri = "mongodb://%s:%s@%s" % (
            quote_plus("root"), quote_plus("root360"), "192.168.44.101:27100")
        return pymongo.MongoClient(uri)
    
    
    stm = SchedulerTaskManager(create_default_client())
    stm.start_command_process("1", ["python3", "lala.py"])
    while True:
        stm.refresh_process()
        import time
        
        time.sleep(10)
