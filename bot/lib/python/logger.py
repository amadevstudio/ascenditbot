import sys
import os
import datetime
# import queue
# import threading
import logging


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
        self.__last_datetime = None

        self.file = file

        # self.__write_queue = queue.Queue()

        self.__reinit_logger()

        # write_thread = threading.Thread(target=self.__writer)
        # write_thread.daemon = True
        # write_thread.start()

    def __reinit_logger(self):
        current_time = datetime.datetime.now()
        if self.__last_datetime is not None and self.__last_datetime.day == current_time.day:
            return

        self.__last_datetime = current_time
        self.__set_dated_filename(now=current_time)

        if os.environ['ENVIRONMENT'] == "development":
            logging.basicConfig(encoding='utf-8')  # , level=logging.DEBUG)
        else:
            logging.basicConfig(filename=self.dated_filepath, encoding='utf-8', level='INFO')
        self.logger = logging.getLogger(self.file)

    # def __writer(self):
    #     while True:
    #         result = self.__write_queue.get()
    #         result = result.encode('utf-8')
    #         with open(f"{self.__bot_path}/log/{self.dated_file}.log", "ab") as f:  # add in binary mode
    #             f.write(result)

    def __set_dated_filename(self, now=None):
        if now is None:
            now = datetime.datetime.now()
        dated_filename = self.file + "_" + now.strftime("%d_%m_%Y")
        self.dated_filepath = os.path.join(self.__logs_folder, dated_filename)

    # [12:49:41 26.06.1998] LEVEL arg1 args2
    def __out_log(self, *args, level="log"):
        result = ""

        now = datetime.datetime.now()

        human_now = "[" + now.strftime("%H:%M:%S %d.%m.%Y") + "]"
        result += human_now + " "

        result += (self.LEVELS[level] if level in self.LEVELS else "EMLVL") + " "

        if len(args) > 0:
            for arg in args:
                result += str(arg) + " "
            result = result[0:-1]

        if os.environ['ENVIRONMENT'] != "development" and self.file is not None:
            self.__reinit_logger()
            # self.__set_dated_filename(now)
            # self.__write_queue.put(result)
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


# logger = Logger()
