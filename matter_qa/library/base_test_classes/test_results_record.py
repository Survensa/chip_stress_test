from mobly.records import TestResultEnums, TestResultRecord, ExceptionRecord
import mobly.utils as utils
from enum import Enum, auto

class ResultsRecordTypeEnums:
    SummaryRecordType = "Summary Record"
    DUTNodeInformationRecordType = "DUT Record"
    IterationRecordType = "Iteration Record"
class DUTInformationRecordEnums:
    RECORD_VENDOR_NAME  = "Vendor Name"
    RECORD_PRODUCT_NAME = "Product Name"
    RECORD_PRODUCT_ID   = "Product Id"
    RECORD_VENDOR_ID    = "Vendor Id"
    RECORD_SOFTWARE_VERSION = "Software Version"
    RECORD_HARDWARE_VERSION = "Hardware Version"
    RECORD_PLATFORM = "Platform"
    RECORD_COMMISSIONING_METHOD = "Commissioning-method"
class DUTInformationRecord:
    def __init__(self) -> None:
        self.record_dict = {}
        self.record_dict[DUTInformationRecordEnums.RECORD_VENDOR_NAME] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_PRODUCT_NAME] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_PRODUCT_ID] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_VENDOR_ID] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_SOFTWARE_VERSION] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_HARDWARE_VERSION] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_PLATFORM] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_COMMISSIONING_METHOD] = None
    
    def update_record(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(DUTInformationRecordEnums,k):
                self.record_dict.update(k,v)

class SummaryTestResultsEnums:
    RECORD_TEST_NAME = "Test Case Name"
    RECORD_TEST_CASE_ID = "Test Case ID"
    RECORD_TEST_CLASS = "Test Case Class"
    REPORT_TEST_BEGIN_TIME = "Test Case Beginned at"
    REPORT_TEST_END_TIME = "Test Case Ended at"
    RECORD_TEST_COMPLETION_STATUS = "test_compleition_status"
    RECORD_TEST_STATUS = "TestCase Status"
    RECORD_TEST_COMPLETED = "Test Completed"
    RECORD_TEST_IN_PROGRESS = "Test In Progress"
    RECORD_TOTAL_NUMBER_OF_ITERATIONS = "Total number of iterations"
    RECORD_NUMBER_OF_ITERATIONS_COMPLETED = "number of iterations completed"
    RECORD_NUMBER_OF_ITERATIONS_PASSED = "number of iterations Passed"
    RECORD_NUMBER_OF_ITERATIONS_FAILED = "number of iterations Failed"
    RECORD_LIST_OF_ITERATIONS_FAILED = "List of Iterations Failed"
 
                
class SummaryTestResultRecord:
    def __init__(self, **kwargs) -> None:
        self.record_dict = {}
        self.record_dict[SummaryTestResultsEnums.RECORD_TEST_NAME] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_TEST_CASE_ID] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_TEST_CLASS] = None
        self.record_dict[SummaryTestResultsEnums.REPORT_TEST_BEGIN_TIME] = None
        self.record_dict[SummaryTestResultsEnums.REPORT_TEST_END_TIME] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_TEST_COMPLETION_STATUS] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_TEST_STATUS] = SummaryTestResultsEnums.RECORD_TEST_IN_PROGRESS
        self.record_dict[SummaryTestResultsEnums.RECORD_TOTAL_NUMBER_OF_ITERATIONS] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_COMPLETED] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_PASSED] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_FAILED] = None
        self.record_dict[SummaryTestResultsEnums.RECORD_LIST_OF_ITERATIONS_FAILED] = []

    def update_record(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(SummaryTestResultsEnums,k):
                self.record_dict.update(k,v)

class IterationTestResultsEnums:
    RECORD_ITERATION_NUMBER = 'Iteration Number'
    RECORD_ITERATION_BEGIN_TIME = 'Iteration Begin Time'
    RECORD_ITERATION_END_TIME = 'Iteration End Time'
    RECORD_ITERATION_RESULT = 'Iteration Result'
    RECORD_ITERATION_RESULT_PASS = 'PASS'
    RECORD_ITERATION_RESULT_FAIL = 'FAIL'
    RECORD_ITERATION_RESULT_SKIP = 'SKIP'
    RECORD_ITERATION_RESULT_ERROR = 'ERROR'

class IterationTestResultRecord(TestResultRecord):
    def __init__(self, test_name, test_class, iteration_number):
        self.record_dict = {}
        self.record_dict[IterationTestResultsEnums.RECORD_ITERATION_NUMBER] = None
        self.record_dict[IterationTestResultsEnums.RECORD_ITERATION_BEGIN_TIME] = None
        self.record_dict[IterationTestResultsEnums.RECORD_ITERATION_END_TIME] = None
        self.record_dict[IterationTestResultsEnums.RECORD_ITERATION_RESULT] = None

    def update_record(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(IterationTestResultsEnums,k):
                self.record_dict.update(k,v)

    def iteration_begin(self, iteration_number):
        self.iteration_begin_time = utils.get_current_epoch_time()
        self.current_iteration = iteration_number
        
    def iteration_pass(self):
        self._iteration_end(TestResultEnums.TEST_RESULT_PASS)

    def iteration_fail(self, e=None):
        self._iteration_end(TestResultEnums.TEST_RESULT_FAIL, e)

    def iteration_end(self, iteration_result_data, e=None):
        if self.iteration_begin_time is not None:
            self.iteration_end_time = utils.get_current_epoch_time()
        self.iteration_result = iteration_result_data.get(IterationTestResultsEnums.RECORD_ITERATION_RESULT)
        self.current_iteration = iteration_result_data.get(IterationTestResultsEnums.RECORD_ITERATION_NUMBER)
        if e:
            self.iteation_termination_signal = ExceptionRecord(e)
    

class TestresultsRecord():
    def __init__(self, summary_record=None, dut_record=None, iter_record=None) -> None:
        self.summary_result_record = SummaryTestResultRecord(summary_record)
        self.device_information_record = DUTInformationRecord()
        self.test_iteration_result_record = IterationTestResultRecord()

    