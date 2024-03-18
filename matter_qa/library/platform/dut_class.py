import logging
import os
from matter_qa.library.base_test_classes.dut_base_class import BaseDutNodeClass

log = logging.getLogger("dut")
class dut_class(BaseDutNodeClass):
    def __init__(self) -> None:
        super().__init__()

    def reboot_dut(self):
        log.info("I am in dut class reboot")

    def factory_reset_dut(self):
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