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
            logging.basicConfig(encoding='utf-8')  # , level=logging.DEBUG)
        else:
            file_path = os.path.join(self.__logs_folder, self.__file)
            file_handler = TimedRotatingFileHandler(file_path, when='D', interval=1)
            logging.basicConfig(encoding='utf-8', level='INFO', handlers=[file_handler])
        self.logger = logging.getLogger(self.__file)

    # [12:49:41 26.06.1998] LEVEL arg1 args2
    def __out_log(self, *args, level="log"):
        result = ""

        # # Logging module add datetime and level automatically
        # now = datetime.datetime.now()
        # human_now = "[" + now.strftime("%H:%M:%S %d.%m.%Y") + "]"
        # result += human_now + " "
        # result += (self.LEVELS[level] if level in self.LEVELS else "EMLVL") + " "

        if len(args) > 0:
            for arg in args:
                result += str(arg) + " "
            result = result[0:-1]

        if os.environ['ENVIRONMENT'] != "development" and self.__file is not None:
            getattr(self.logger, level)(result)
        else:
            print(result, flush=True)

    def log(self, *args):
        self.__out_log(*args, "\n", level="info")

    def warn(self, *args):
        self.__out_log(*args, "\n", level="warning")

    # works only in error
    # args (for self.__out_log) = [arg1, arg2, | Details:, exc_type, exc_obj, fename, :, exc_tb.tb_lineno]
    def err(self, *args):
        exc_type, exc_obj, exc_tb = sys.exc_info()

        details = str(exc_type) + " " + str(exc_obj)
        if exc_tb is not None:
            fename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            details += " " + str(fename) + ":" + str(exc_tb.tb_lineno)

        self.__out_log(
            *args, "| Details:", details, "\n", level="err")
