import logging
import datetime
import os
import traceback
import time
import importlib
import sys

from matter_qa.library.helper_libs.logger import qa_logger
from matter_qa.library.helper_libs.exceptions import *
from matter_qa.library.helper_libs.utils import default_config_reader
from matter_qa.library.platform.dut_class import dut_class
from matter_qa.library.helper_libs.matter_testing_support import MatterBaseTest
from matter_qa.configs.config import TestConfig

from mobly.config_parser import ENV_MOBLY_LOGPATH, TestRunConfig

import chip
from chip.exceptions import ChipStackError

log = logging.getLogger("base_tc")
class MatterQABaseTestCaseClass(MatterBaseTest):
    def __init__(self,*args) -> None:
        self.iteration_log_created = False
        super().__init__(*args)
        self._start_test()
        
    def _start_test(self,**kwargs):
        
        self.test_config = self._config_reader(config=kwargs.get("test_config"))
        self.run_set_folder = self._create_run_set_folder()
        # need this logger to create log file for every iteration
        self.qa_logger = qa_logger()
        # create a dut object to use in TC
        self.dut = self._get_dut_obj()

    def _config_reader(self, config=None):
        test_config = TestConfig(self.matter_test_config.reliability_tests_config)
        # to over write any default config parameters
        test_config = self._overwrite_test_config(test_config)
        return test_config

    def _overwrite_test_config(self,test_config):
        """
        overwrite the test config with test case specific parameters
        """
        if hasattr(test_config, 'test_case_config') and hasattr(getattr(test_config,'test_case_config'), type(self).__name__) :
          test_config.general_configs.number_of_iterations = getattr(test_config.test_case_config, type(self).__name__).number_of_iterations
        return test_config
    
    def _create_run_set_folder(self):
        run_set_folder = "RUN_SET_" + datetime.datetime.now().strftime("%d_%b_%Y_%H-%M-%S")
        runset_folder_path = self.test_config.general_configs.logFilePath
        if not os.path.exists(runset_folder_path):
            if os.path.exists(os.path.dirname(runset_folder_path)):
                os.mkdir(runset_folder_path)
            else:
               runset_folder_path = os.getcwd()
        runset_folder_path = os.path.join(runset_folder_path,run_set_folder)
        self.test_config.runset_folder_path = runset_folder_path
        os.mkdir(runset_folder_path)
        return runset_folder_path
    
    def _create_iteration_log_file(self,iteration_count):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # TODO : Fix the path here
        try :
            self.iter_log_path = os.path.join(self.run_set_folder, str(iteration_count))
            if not os.path.exists(self.iter_log_path):
                os.makedirs(self.iter_log_path)
            log_filename = os.path.join(self.iter_log_path, f"log_{timestamp}.log")
            self.iteration_log = self.qa_logger.create_log_file(log_filename)
            log.info("Started Iteration {}".format(iteration_count))
            self.iteration_log_created = True
            self.test_config.iter_log_path = self.iter_log_path
        except Exception as e:
            log.error("Failed to create iteration log file {e}".format(e))
            sys.exit(1)
        
    def _get_dut_obj(self):
        module = self._import_platorm()
        return self._create_dut_obj(module)
    
    def _import_platorm(self):
        try:
            platform = self.test_config.general_configs.platform_execution
            if hasattr(self.test_config.dut_config,platform):
                dut_platform = getattr(self.test_config.dut_config, platform)
                # import platform specific module
                module = importlib.import_module(dut_platform.module)
                return module
            else:
                log.error("DUT module not available")
                sys.exit()
        except Exception as e:
            logging.error("Error loading dut module: {}".format(e))
            traceback.print_exc()
            sys.exit()

    def _create_dut_obj(self,module):
        return module.create_dut_object(self.test_config)
    
    def pre_iteration(self, iteration_count):
        if not self.iteration_log_created:
            self._create_iteration_log_file(iteration_count)
        self.dut.pre_iteration_loop()
    
    def post_iteration(self):
        self.dut.post_iteration_loop()
        log.info("Test Iteration Completed")
        self.qa_logger.close_log_file(self.iteration_log)
        # set this flag to create log in next iteration
        self.iteration_log_created = False
    
    def end_of_test(self):
        print("I am in base class end of test ")
    
    def iterate_tc(iterations=1):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                print("Decorator parameter:", iterations)
                for i in range(1,iterations+1):
                    self.pre_iteration(i)
                    self.test_config.current_iteration = i
                    try:
                        result = func(*args, **kwargs)
                        self.update_analytics()
                    except IterationError as e:
                        print("I got exception, failed iteration {}".format(i))
                        logging.error(e, exc_info=True)
                        self.update_iteration_logs()
                        #return result# you dont need this
                    self.post_iteration()
                self.end_of_test()
            return wrapper
        return decorator

    def update_analytics(self):
        pass

    def update_iteration_logs(self):
        pass

    def pair_dut(self) -> bool:
        try:
            # TODO pass list idx as 0 for now as we are using default nodeID _DEFAULT_DUT_NODE_ID
            if self._commission_device(0):
                return True
        except Exception as e:
            pairing_result = {"status": "failed", "failed_reason": str(e)}
            tb = traceback.format_exc()
            raise TestCaseError(pairing_result,tb)
     
    
    def unpair_dut(self, controller=None, node_id=None) -> dict:
        try:
            if controller is None and node_id is None:
                controller = self.default_controller

            controller.UnpairDevice(self.dut_node_id)
            time.sleep(3)
            controller.ExpireSessions(self.dut_node_id)
            time.sleep(3)
            log.info("unpair_dut completed successfully")
            return True
        
        except Exception as e:
            logging.error(e, exc_info=True)
            unpair_result = {"status": "failed", "failed_reason": e.msg}
            if isinstance(e, chip.exceptions.ChipStackError):
                #TODO handle this properly -- Check
                unpair_result = {"status": "failed", "failed_reason": e.msg}
            tb = traceback.format_exc()
            raise TestCaseError(unpair_result,tb)


dut_objects_list = []

def test_start(test_class_name):
    try:
        global dut_objects_list
        dict_args = convert_args_dict(sys.argv[1:])
        arg_keys = dict_args.keys()
        if "--yaml-file" in arg_keys:
            test_config = yaml_config_reader(dict_args)
        else:
            test_config = default_config_reader()
        test_config.test_class_name = test_class_name
        MatterQABaseTestCaseClass.test_config = test_config  # initialise the base class with configs
        log_path = test_config.general_configs.logFilePath
        if log_path is not None and os.path.exists(log_path):
            run_set_path = run_set_folder_path(datetime.datetime.now(), log_path)
            log_path = os.path.join(run_set_path, test_config.test_class_name)
            log_path_add_args(log_path)  # this function will set log storage path for mobly
            test_config.general_configs.logFilePath = log_path
        else:
            run_set_path = run_set_folder_path(datetime.datetime.now(), os.getcwd())
            log_path = os.path.join(run_set_path, test_config.test_class_name)
            log_path_add_args(path=log_path)
            test_config.general_configs.logFilePath = log_path

        log_info_init(test_config)  # updating config dict with iter_log_dir and current_iter

        # Function will set the commissioning method for matter_support testing file
        add_args_commissioning_method(test_config.general_configs.commissioning_method)
        dut_object_loader(test_config, dut_objects_list)
    except Exception as e:
        logging.error(e, exc_info=True)
        traceback.print_exc()
