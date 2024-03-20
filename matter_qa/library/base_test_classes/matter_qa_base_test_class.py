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
from matter_qa.library.base_test_classes.test_results_record import TestresultsRecord,ResultsRecordType, TestResultEnums,IterationTestResultsEnums,SummaryTestResultsEnums

from .test_result_observable import TestResultObservable
from .test_result_observer import TestResultObserver

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
        self.test_result_observable = TestResultObservable()
        #TODO fix this file business properly
        summary_file = os.path.join(self.run_set_folder, 'summary.json')
        iterations_file = os.path.join(self.run_set_folder, 'iterations.json')
        self.test_result_observer = TestResultObserver(summary_file,iterations_file)
        self.test_result_observable.subscribe(self.test_result_observer)

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
        """
                here we will set the path for storing the iteration logs. We are re-using the directories created by mobly framework
                mobly will create a runset id and folder like '03-19-2024_12-36-26-432'
                iteration wise data will be stored in the directory <log_path>/MatterTest/<run-set>/<test_case_name>
                if this path does not exist then current directory will be used.

                self.root_output_path -> created by mobly will have structure of <log_path>/MatterTest/<run-set>
                self.TAG -> created by mobly will have test_class_name
                """
        run_set_folder_path = os.path.join(self.root_output_path, self.TAG)
        if not os.path.exists(run_set_folder_path):
            run_set_folder_path = os.path.join(os.getcwd(), datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S-%f"),
                                               self.TAG)
            os.mkdir(run_set_folder_path)
        self.test_config.runset_folder_path = run_set_folder_path
        return run_set_folder_path
    
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
    
    def pre_iteration(self, iteration_number):
        if not self.iteration_log_created:
            self._create_iteration_log_file(iteration_number)
        self.dut.pre_iteration_loop()
        self.summary_record = TestresultsRecord.create_record(ResultsRecordType.SummaryRecordType,
                                                self.tc_name,type(self).__name__)
        self.summary_record.summary_record_begin(self.test_config.general_configs.number_of_iterations)


        self.iteration_result_record = TestresultsRecord.create_record(ResultsRecordType.IterationRecordType,
                                                         self.tc_name,type(self).__name__,iteration_number )
        self.iteration_result_record.iteration_begin(iteration_number)
        

    def post_iteration(self, iteration_number, iteration_result,e=None):
        self.dut.post_iteration_loop()
        log.info("Test Iteration Completed")
        self.qa_logger.close_log_file(self.iteration_log)
        # set this flag to create log in next iteration
        self.iteration_log_created = False

        iteration_result_data = {IterationTestResultsEnums.RECORD_ITERATION_NUMBER : iteration_number,
                                 IterationTestResultsEnums.RECORD_ITERATION_RESULT : iteration_result}
        
        self.iteration_result_record.iteration_end(iteration_result_data,e)
        summary_result_data = {SummaryTestResultsEnums.RECORD_TEST_STATUS: SummaryTestResultsEnums.RECORD_TEST_COMPLETED}
        self.summary_record.summary_record_end(summary_result_data)
        self.test_result_observable.notify(self.iteration_result_record)
        self.test_result_observable.notify(self.summary_record)
    
    def end_of_test(self):
        print("I am in base class end of test ")
    
    def iterate_tc(iterations=1):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                print("Decorator parameter:", iterations)
                for current_iteration in range(1,iterations+1):
                    self.pre_iteration(current_iteration)
                    self.test_config.current_iteration = current_iteration
                    try:
                        result = func(*args, **kwargs)
                        iteration_test_result = TestResultEnums.TEST_RESULT_PASS
                        self.update_analytics()
                    except IterationError as e:
                        print("I got exception, failed iteration {}".format(current_iteration))
                        logging.error(e, exc_info=True)
                        self.update_iteration_logs()
                        iteration_test_result = TestResultEnums.TEST_RESULT_FAIL
                        #return result# you dont need this
                    self.post_iteration(current_iteration, iteration_test_result)
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
