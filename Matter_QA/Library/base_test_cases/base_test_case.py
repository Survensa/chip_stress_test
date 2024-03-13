import logging
import datetime
import os

from matter_qa.library.helper_libs.exceptions import IterationError
from matter_qa.library.helper_libs.logger import log, qa_logger
from matter_qa.library.helper_libs.utils import default_config_reader
from matter_qa.library.helper_libs import utils as utils
from matter_qa.library.platform.dut_class import dut_class

class BaseTestCase(object):
    def __init__(self) -> None:
        self.iteration_log_created = False
        pass
    def start_test(self,**kwargs):
        """
        This function called by test runner
            Parameters:
                kwargs: Dictionary of Config Object,logger, dut 
                
            Returns:
                None
        """
        self.test_config = self._config_reader(config=kwargs.get("test_config"))
        self.test_config = self._overwrite_test_config()
        self.run_set_folder = self._create_run_set_folder()
        self._register_loggers(logger_obj=kwargs.get("logger_obj"))
        self.dut =  dut_class()
    
    def _register_loggers(self, logger_obj):
        self.qa_logger = qa_logger()
        log.register_looger(self.qa_logger)
        if logger_obj and isinstance(log.log_interface): 
            log.register_looger(logger_obj)

    def _config_reader(self, config=None):
        test_config = default_config_reader()
        if config and isinstance(utils.TestConfig):
            utils.TestConfig(config)
        return test_config

    def _overwrite_test_config(self):
        """
        overwrite the test config with test case specific parameters
        """
        if hasattr(self.test_config, 'test_cases_configs') and hasattr(self.test_config.test_cases_configs,type(self).__name__):
            self.test_config.general_configs.number_of_iterations = getattr(self.test_config.test_cases_configs, type(self).__name__).number_of_iterations
        return self.test_config
    
    def _create_run_set_folder(self):
        runset_folder_path = self.test_config.general_configs.logFilePath
        run_set_folder = "RUN_SET_" + datetime.datetime.now().strftime("%d_%b_%Y_%H-%M-%S")
        if not os.path.exists(runset_folder_path):
            if os.path.exists(os.path.dirname(runset_folder_path)):
                os.mkdir(runset_folder_path)
            else:
               runset_folder_path = os.getcwd()
            runset_folder_path = os.path.join(runset_folder_path,run_set_folder)
        os.mkdir(runset_folder_path)
        return runset_folder_path
    
    def _create_iteration_log_file(self,iteration_count):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # TODO : Fix the path here
        tc_log_path = os.path.join(self.run_set_folder, str(iteration_count))
        if not os.path.exists(tc_log_path):
            os.makedirs(tc_log_path)
        log_filename = os.path.join(tc_log_path, f"log_{timestamp}.log")
        self.iteration_log = self.qa_logger.create_log_file(log_filename)
        log.info("Started Iteration {}".format(iteration_count))
        self.iteration_log_created = True

    def pre_iteration(self, iteration_count):
        if not self.iteration_log_created:
            self._create_iteration_log_file(iteration_count)
        log.info("I am in base class pre-iteration ")
        log.error("this is test error")
        self.dut.pre_iteration_loop()
        self.dut.start_logging()
    
    def post_iteration(self):
        log.debug("I am in base class post-iteration ")
        log.info("Done with Iteration")
        self.dut.post_iteration_loop()
        self.qa_logger.close_log_file(self.iteration_log)
        # set this flag to create log in next iteration
        self.iteration_log_created = False
    
    def end_of_test(self):
        print("I am in base class end of test ")
    
    def iterate_tc(iterations=5):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                print("Decorator parameter:", iterations)
                for i in range(1,iterations):
                    self.pre_iteration(i)
                    try:
                        result = func(*args, **kwargs)
                    except IterationError:
                        print("I got exception, failed iteration {}".format(i))
                #return result# you dont need this
                    self.post_iteration()
                self.end_of_test()
            return wrapper
        return decorator
