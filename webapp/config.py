"""
默认配置模块
"""
import os
import platform

system = "windows" if platform.system().lower().find("windows") >= 0 else "other"


class LogConfig:
    _filepath = os.path.split(os.path.abspath(__file__))[0]
    LOG_PATH = os.path.join(os.path.split(_filepath)[0], "logs")
    APP_SLOW_LOG = 1


class DefaultConfig(LogConfig):
    SECRET_KEY = "the secret key"
    QUALITY_EXPORT_DIRECTORY = os.environ.get("QUALITY_EXPORT_DIRECTORY")
    if QUALITY_EXPORT_DIRECTORY is None:
        if system == "windows":
            QUALITY_EXPORT_DIRECTORY = r"D:\quality_report"
        else:
            QUALITY_EXPORT_DIRECTORY = r"/mnt/data/360_manager_quality_report"