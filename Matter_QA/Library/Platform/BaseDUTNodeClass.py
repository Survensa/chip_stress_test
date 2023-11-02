from abc import ABC, abstractmethod

class BaseNodeDutClass(ABC):

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
    pass

def create_dut_object():
    pass