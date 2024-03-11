from Matter_QA.Library.BaseTestCases.dut_base_class import BaseDutNodeClass
from Matter_QA.Library.HelperLibs.Logger import log



class dut_class(BaseDutNodeClass):
    
    def reboot_dut(self):
        log.info("I am in dut class reboot")

    def factory_reset_dut(self,reset=True):
        log.info("I am in dut class factory_reset_dut")
    
    def start_matter_app(self):
        log.info("I am in dut class start_matter_app")

    def start_logging(self):
        log.info("I am in dut reboot class")
    
    def stop_logging(self):
        log.info("I am in dut class start_logging")

    def pre_iteration_loop(self):
        log.info("I am in dut class pre_iteration_loop")
    
    def post_iteration_loop(self):
        log.info("I am in dut class post_iteration_loop")