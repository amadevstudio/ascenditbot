import sys
import os
import datetime
# import queue
# import threading
import logging
from logging.handlers import TimedRotatingFileHandler


class Logger:
    LEVELS = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL"
    }

    def __init__(self, logs_folder, file="out"):
        self.__logs_folder = logs_folder
        self.__file = file
        self.__init_logger()

    def __init_logger(self):
        if os.environ['ENVIRONMENT'] == "development":
            logging.basicConfig(
                encoding='utf-8',
                format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S %z')  # , level=logging.DEBUG)
        else:
            file_path = os.path.join(self.__logs_folder, self.__file)
            file_handler = TimedRotatingFileHandler(file_path, when='D', interval=1)
            logging.basicConfig(
                encoding='utf-8',
                format='%(asctime)s %(levelname)-8s %(message)s',
                level='INFO',
                handlers=[file_handler],
                datefmt='%Y-%m-%d %H:%M:%S %z')
        self.logger = logging.getLogger(self.__file)

    # [12:49:41 26.06.1998] LEVEL arg1 args2
    def __out_log(self, *args, level="log"):
        result = ""

        # # Logging module add datetime and level automatically
        # now = datetime.datetime.now().astimezone()
        # human_now = "[" + now.strftime("%H:%M:%S %d.%m.%Y %z") + "]"
        # result += human_now + " "
        # result += (self.LEVELS[level] if level in self.LEVELS else "EMLVL") + " "

        if len(args) > 0:
            for arg in args:
                result += str(arg) + " "
            result = result[0:-1]

        getattr(self.logger, level)(result)

    def log(self, *args):
        self.__out_log(*args, "\n", level="info")

    def warn(self, *args):
        self.__out_log(*args, "\n", level="warning")

    # works only in error
    # args (for self.__out_log) = [arg1, arg2, | Details:, exc_type, exc_obj, fename, :, exc_tb.tb_lineno]
    def err(self, *args):
        if os.environ['ENVIRONMENT'] == "production":
            exc_type, exc_obj, exc_tb = sys.exc_info()

            details = str(exc_type) + " " + str(exc_obj)
            if exc_tb is not None:
                fename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                details += " " + str(fename) + ":" + str(exc_tb.tb_lineno)

            self.__out_log(
                *args, "| Details:", details, "\n", level="err")
        else:
            raise(args[0])
