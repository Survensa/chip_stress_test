import logging
import inspect
import sys
from abc import ABC, abstractmethod

class log_interface(object):

    @abstractmethod
    def info(self, msg):
        pass
   
    @abstractmethod
    def debug(self, msg):
        pass

    @abstractmethod
    def error(self, msg):
        pass

    @abstractmethod
    def warning(self, msg):
        pass

    @abstractmethod
    def critical(self, msg):
        pass
    
class qa_logger(log_interface):
    
    def __init__(self,name='') -> None:
        log = logging.getLogger(name)
        log.setLevel(logging.NOTSET)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.NOTSET)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        #formatter = ModuleNameFormatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        log.addHandler(console_handler)
        self.log = log

    def create_log_file(self,log_file_name):
        self.log_file_handler= logging.FileHandler(log_file_name)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_file_handler.setFormatter(formatter)
        self.log_file_handler.setLevel(logging.NOTSET)
        # Add the file handler to the logger
        self.log.addHandler(self.log_file_handler)
        return self.log_file_handler
    
    def close_log_file(self, log_file_handler):
        self.log.removeHandler(log_file_handler)
        log_file_handler.close()

    def info(self, msg):
        """ 
        frm = inspect.stack()[1]
        f = sys._current_frames()
        frame=inspect.currentframe()
        frame=frame.f_back.f_back
        code = frame.f_code
        print(code.co_filename)
        """
        self.log.info(msg)

    def debug(self, msg):
        self.log.debug(msg)
    
    def error(self, msg):
        self.log.error(msg)
    
    def warning(self, msg):
        self.log.warning(msg)
    
    def critical(self, msg):
        self.log.critical(msg)
    
    def get_logger_bkup(self, name):
        log = logging.getLogger(name)
        log.setLevel(logging.NOTSET)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.NOTSET)
        #formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        console_handler.setFormatter(formatter)
        log.addHandler(console_handler)
        return log
    
    def get_logger(self):
        return self.log

class Log(log_interface):

    def __init__(self) -> None:
        super().__init__()
        self.logger_objs_list =[]
    
    def register_looger(self, logger_obj):
        if isinstance(logger_obj,log_interface) and logger_obj not in self.logger_objs_list:
            self.logger_objs_list.append(logger_obj)
    
    def info(self, msg):
        self._log_msg('info', msg)
   
    def debug(self, msg):
        self._log_msg('debug', msg)

    def error(self, msg):
        self._log_msg('error', msg)

    def warning(self, msg):
        self._log_msg('warning', msg)

    def critical(self, msg):
        self._log_msg('critical', msg)
    
    def _log_msg(self, level, msg):
        for logger_obj in self.logger_objs_list:
            func = getattr(logger_obj, level)
            func(msg)

log = Log()