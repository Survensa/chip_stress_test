from Matter_QA.Library.Platform.BaseDUT import BaseDutClass


class CustomDut(BaseDutClass):
    """This class will be overriden by the user for different devices
    the user will have to populate these fucntions when writing the test case
    each dut will have its own method for reset which they have implemet themselves
    the code below is written as an example for demo puposes
    """

    def reboot(self):
        pass

    def factory_reset(self, i, iteration):
        pass

    def advertise(self, iteration):
        pass

    def start_logging(self, file_name):
        pass

    def stop_logging(self):
        pass

