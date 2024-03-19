from mobly.records import TestResultEnums, TestResultRecord, ExceptionRecord
import mobly.utils as utils
from enum import Enum, auto

class ResultsRecordType(Enum):
    SummaryRecordType = "Summary Record"
    IterationRecordType = "Iteration Record"

class IterationTestResultsEnums(TestResultEnums):
    RECORD_ITERATION_NUMBER = 'Iteration Number'
    RECORD_ITERATION_RESULT = 'Iteration Result'
    RECORD_ITERATION_BEGIN_TIME = 'Iteration Begin Time'
    RECORD_ITERATION_END_TIME = 'Iteration End Time'
    RECORD_ITERATION_RESULT_PASS = 'PASS'
    RECORD_ITERATION_RESULT_FAIL = 'FAIL'
    RECORD_ITERATION_RESULT_SKIP = 'SKIP'
    RECORD_ITERATION_RESULT_ERROR = 'ERROR'

class SummaryTestResultsEnums(Enum):
    RECORD_TEST_STATUS = "TestCase Status"
    RECORD_TEST_COMPLETION_STATUS = "test_compleition_status"
    RECORD_TEST_COMPLETED = "Test Completed"
    RECORD_TEST_IN_PROGRESS = "Test In Progress"

class SummaryTestResultRecord(TestResultRecord):
    def __init__(self, test_name, test_class) -> None:
        self.number_of_iteartions = None
        self.number_of_iteartions_passed = None
        self.number_of_iteartions_failed = None
        self.list_of_iterations_failed = []
        self.platform = None
        self.commissioning_method = None 
        self.test_completion_status = None
        self.test_begin_time = None
        self.test_end_time = None
        super().__init__(test_name, test_class)

    def summary_record_begin(self, number_of_iterations):
        self.test_begin_time = utils.get_current_epoch_time()
        self.number_of_iteartions = number_of_iterations
        self.test_completion_status = SummaryTestResultsEnums.RECORD_TEST_IN_PROGRESS

    def summary_record_end(self, *record_data):
        self.test_end_time = utils.get_current_epoch_time()
        #TODO handle the record data properly.
        self.test_completion_status = SummaryTestResultsEnums.RECORD_TEST_COMPLETED

    def to_dict(self):
        return super().to_dict()


class IterationTestResultRecord(TestResultRecord):
    def __init__(self, test_name, test_class, iteration_number):
        self.current_iteration = iteration_number
        self.iteration_begin_time = None
        self.iteration_end_time = None
        self.iteration_result = None
        self.iteation_termination_signal = None
        super().__init__(test_name, test_class)

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
    
    def to_dict(self):
        return super().to_dict()

class TestresultsRecord():
    @staticmethod
    def create_record(record_type,test_name, test_class, iteration_number=None):
        if record_type == ResultsRecordType.SummaryRecordType:
            return SummaryTestResultRecord(test_name, test_class)
        elif record_type == ResultsRecordType.IterationRecordType:
            return IterationTestResultRecord(test_name, test_class,iteration_number)
        else:
            raise ValueError("Invalid record type")