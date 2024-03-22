from .test_observer import Observable,Observer
from .test_results_record import IterationTestResultsEnums
import matter_qa.library.base_test_classes.test_results_record as tr
import json
import os
import logging
import sys

class TestResultObserver(Observer):
    def __init__(self, file_tc_summary):
        self.file_tc_summary = file_tc_summary

    def dispatch(self, record):
        # if file doesnt exist
        if not os.path.exists(self.file_tc_summary):
            # File doesn't exist, create it and write default data
            with open(self.file_tc_summary, 'w') as file:
                json_data = {IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST:[]}
                json_data.update(record.summary_result_record.record) 
                json_data.update(record.device_information_record.record)
                json_data[IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST].append(
                    record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD])
                json.dump(json_data, file)
        else:
            with open(self.file_tc_summary, 'r') as file:
                try:
                    json_data = json.load(file)
                except Exception as e:
                    logging.info('Error loading JSON file: {}'.format(e))
                    sys.exit(1)
                summary_record = json_data[tr.ResultsRecordTypeEnums.SummaryRecordType]
                for k, v in record.summary_result_record.record[tr.ResultsRecordTypeEnums.SummaryRecordType].items():
                    summary_record[k] = v
                dev_record = json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType]
                for k, v in record.device_information_record.record[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType].items():
                    dev_record[k] = v
                list_of_iterations_dict = []
                # append the test iteration result to the list of existing iterations.
                list_of_iterations_dict= json_data[tr.IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST]
                # we get only iteration record
                iteration_number = record.test_iteration_result_record.record[tr.IterationTestResultsEnums.RECORD_ITERATION_RECORD][IterationTestResultsEnums.RECORD_ITERATION_NUMBER]
                if len(list_of_iterations_dict) < iteration_number :
                    list_of_iterations_dict.append(record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD])
                else:
                    list_of_iterations_dict[iteration_number-1] = record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD]

                """
                iter_record = list_of_iterations_dict[iteration_number-1]
                updated_iter_record = self.update_record(iter_record, record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD])
                list_of_iterations_dict[iteration_number-1] = updated_iter_record
                """
                
                json_data[tr.ResultsRecordTypeEnums.SummaryRecordType] = summary_record
                json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType] = dev_record
                json_data[tr.IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST] = list_of_iterations_dict
            
            with open(self.file_tc_summary, 'w') as file_write:
                json.dump(json_data, file_write)
                
    def update_record(self, old_dict: None, new_dict=None):
        """
        The new_dict can have a single key, value pair or a tuple with keys and the value, something like example
        new_dict = {"new_levl":"Test",('level1','sublevel1','analytics_125'):900, ('level2','sublevel2','analytics_5'):105}
        any new key will be inserted inside the Iteration Record value.
        """
        for k,v in new_dict.items():
            current_dict = self.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD]
            if isinstance(k,tuple):
                for level in k[:-1]:
                    current_dict = current_dict.setdefault(level, {})
                current_dict[k[-1]] = v
            else:
                self.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD].update({k:v})
        
        return new_dict
