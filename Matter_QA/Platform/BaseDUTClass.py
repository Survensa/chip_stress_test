from abc import ABC, abstractmethod


class BaseDut(ABC):

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def factory_reset(self):
        pass

    @abstractmethod
    def advertise(self):
        pass

    @abstractmethod
    def start_logging(self):
        pass

    @abstractmethod
    def stop_logging(self):
        pass

