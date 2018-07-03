# coding=utf-8
import logging
import os
import time

from webapp.config import LogConfig

base_formatter = "[%(asctime)s %(lineno)04d@%(funcName)s %(levelname)s] %(message)s"
INFO_FORMATTER = logging.Formatter(base_formatter)
WARN_FORMATTER = logging.Formatter(base_formatter + "-%(module)s")
ERROR_FORMATTER = logging.Formatter(base_formatter + "-%(pathname)s")


def archive_log(log_file_path):
    """
    only for small log file。Append write if new file already exists
    """
    if os.path.isfile(log_file_path):
        new_log_file_path = log_file_path + "-" + time.strftime("%Y%m%d")
        if os.path.isfile(new_log_file_path):
            with open(new_log_file_path, "ab") as new_file, open(log_file_path, "rb+") as old_file:
                for line in old_file:
                    new_file.write(line)
            try:
                os.remove(log_file_path)
            except IOError:  # if file handler is in use, the overwrite it
                with open(log_file_path, "w") as old_file:
                    old_file.write("")
        else:
            try:
                os.rename(log_file_path, new_log_file_path)
            except IOError:
                with open(log_file_path, "w") as old_file:
                    old_file.write("")


def wrapstring(string, level=logging.INFO):
    """
    Dye messages when print on screen
    """
    color_dic = {
        logging.INFO: '\033[92m',   # green
        logging.ERROR: '\033[91m',  # red
        logging.WARN: '\033[93m',   # yellow
        logging.DEBUG: '\033[43m',
        "end": "\33[0m"}
    return color_dic[level] + string + color_dic["end"]


def create_file_handler(log_name, level=logging.DEBUG, formatter=INFO_FORMATTER):
    file_handler = logging.FileHandler(log_name)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    return file_handler


def create_stream_handler(level=logging.DEBUG, formatter=INFO_FORMATTER):
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    return stream_handler


def create_time_rotate_handler(log_name, formatter=INFO_FORMATTER):
    """
    MultiProcess may make log loss
    """
    from logging.handlers import TimedRotatingFileHandler
    time_rotate_handler = TimedRotatingFileHandler(filename=log_name, when="midnight", backupCount=30)
    time_rotate_handler.setLevel(logging.INFO)
    time_rotate_handler.setFormatter(formatter)
    return time_rotate_handler


def generate_logger_handler(logger_name, is_stream_handler=True, is_file_handler=True,
                            add_error_log=True, log_level=logging.DEBUG, formatter=INFO_FORMATTER):
    handlers = []
    log_path = LogConfig.LOG_PATH

    if is_file_handler:
        if log_path and not os.path.exists(log_path):
            os.makedirs(log_path)
        log_name = logger_name + ".log"
        log_file_path = os.path.join(log_path, log_name)
        archive_log(log_file_path)
        info_file_handler = create_file_handler(log_file_path, level=log_level, formatter=formatter)
        handlers.append(info_file_handler)
        if add_error_log:
            error_log_name = logger_name + "-error.log"
            error_log_path = os.path.join(log_path, error_log_name)
            archive_log(error_log_path)
            error_file_handler = create_file_handler(error_log_path, level=logging.ERROR, formatter=ERROR_FORMATTER)
            handlers.append(error_file_handler)

    if is_stream_handler:
        stream_handler = create_stream_handler(level=log_level)
        handlers.append(stream_handler)
    return handlers


def create_logger(logger_name, handlers=None, is_stream_handler=True):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    if handlers is None:
        handlers = generate_logger_handler(logger_name, is_stream_handler)
    for handler in handlers:
        logger.addHandler(handler)
    return logger