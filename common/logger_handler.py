# -*- coding: utf-8 -*-
"""
ctrl+c & ctrl+v 过来的
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 日志级别
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(CURRENT_PATH, os.pardir))
LOG_PATH = os.path.join(ROOT_PATH, 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)


class LogHandler(logging.Logger):
    """
    LogHandler
    """

    def __init__(self, name, level=DEBUG, stream=True, file=True):
        self.name = name
        self.level = level
        logging.Logger.__init__(self, self.name, level=level)
        if stream:
            self._set_stream_handler()
        if file:
            self._set_file_handler()

    def _set_file_handler(self, level=None):
        """
        set file handler
        :param level:
        :return:
        """
        file_name = os.path.join(LOG_PATH, '{name}.log'.format(name=self.name))
        # 设置日志回滚, 保存在log目录, 每五天更新一次
        file_handler = TimedRotatingFileHandler(filename=file_name, when='D', interval=5, backupCount=1)
        if not level:
            file_handler.setLevel(self.level)
        else:
            file_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')

        file_handler.setFormatter(formatter)
        self.file_handler = file_handler
        self.addHandler(file_handler)

    def _set_stream_handler(self, level=None):
        """
        set stream handler
        :param level:
        :return:
        """
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        stream_handler.setFormatter(formatter)
        if not level:
            stream_handler.setLevel(self.level)
        else:
            stream_handler.setLevel(level)
        self.addHandler(stream_handler)


class MonitorLoggerHandler(LogHandler):
    def __init__(self, name, level=INFO, stream=True, file=True):
        super().__init__(name, level=level, stream=stream, file=file)

    def _set_file_handler(self, level=None):
        """
        set file handler
        :param level:
        :return:
        """
        file_name = os.path.join(LOG_PATH, '{name}.out'.format(name=self.name))
        # 设置日志回滚, 保存在log目录, 每一天归档一次，不留历史档
        file_handler = TimedRotatingFileHandler(filename=file_name, when='D', interval=1, backupCount=1)
        if not level:
            file_handler.setLevel(self.level)
        else:
            file_handler.setLevel(level)
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        self.file_handler = file_handler
        self.addHandler(file_handler)


if __name__ == '__main__':
    x = MonitorLoggerHandler("hahaha")
    count = 0
    while True:
        x.info("hello %s" % count)
        count += 1
        import time
        time.sleep(1)