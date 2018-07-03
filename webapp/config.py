"""
默认配置模块
"""
import os


class LogConfig:
    _filepath = os.path.split(os.path.abspath(__file__))[0]
    LOG_PATH = os.path.join(os.path.split(_filepath)[0], "logs")
    APP_SLOW_LOG = 1


class DefaultConfig(LogConfig):
    SECRET_KEY = "the secret key"

