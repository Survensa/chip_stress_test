from abc import ABC, abstractmethod

class BaseDutNodeClass(ABC):

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def factory_reset(self, i, iteration):
        pass

    @abstractmethod
    def advertise(self, iteration):
        pass

    @abstractmethod
    def start_logging(self, file_name):
        pass

    @abstractmethod
    def stop_logging(self):
        pass

class BaseNodeDutConfiguration(object):

    def __init__(self, dut_config, test_config) -> None:
        pass
    def get_dut_config():
        pass

def register_dut_object():
    pass