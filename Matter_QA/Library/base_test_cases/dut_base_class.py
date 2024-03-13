from abc import ABC, abstractmethod

class BaseDutNodeClass(ABC):

    @abstractmethod
    def reboot_dut(self):
        pass

    @abstractmethod
    def factory_reset_dut(self, stop_reset):
        """
        this fucntion will factory reset the DUT meaning the matter app will be restarted
        'stop_reset' parameter is used as boolean flag to stop the function from restarting matter app
        """
        pass

    @abstractmethod
    def start_matter_app(self):
        pass

    @abstractmethod
    def start_logging(self, file_name):
        pass

    @abstractmethod
    def stop_logging(self):
        pass

    @abstractmethod
    def pre_iteration_loop(self):
        pass

    @abstractmethod
    def post_iteration_loop(self):
        pass
