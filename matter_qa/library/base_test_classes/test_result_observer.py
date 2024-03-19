from .test_observer import Observable,Observer
from matter_qa.library.base_test_classes.test_results_record import SummaryTestResultRecord, IterationTestResultRecord
import json

class TestResultObserver(Observer):
    def __init__(self, file_tc_summary, file_iterations_summary):
        self.file_tc_summary = file_tc_summary
        self.file_iterations_summary = file_iterations_summary

    def dispatch(self, record):
        if isinstance(record,SummaryTestResultRecord):
            with open(self.file_tc_summary, 'w') as f:
                 json.dump(record.to_dict(), f)
        elif isinstance(record,IterationTestResultRecord):
            with open(self.file_iterations_summary, 'a') as f:
                #TODO 
                json_data= json.dumps(record.to_dict())
                #TODO temp fix, but we need to fix this properly.
                f.write(json_data + '\n')