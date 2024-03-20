from .test_observer import Observable,Observer
import matter_qa.library.base_test_classes.test_results_record as tr
import json
import os

class TestResultObserver(Observer):
    def __init__(self, file_tc_summary):
        self.file_tc_summary = file_tc_summary

    def dispatch(self, record):
        
        #build json dict reading file
        if os.stat(self.file_tc_summary).st_size != 0:
            json_data = json.load(self.file_tc_summary)
            summary_record = json_data[tr.ResultsRecordTypeEnums.SummaryRecordType]
            for k, v in record.summary_result_record.record_dict:
                summary_record[k] = v
            dev_record = json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType]
            for k, v in record.device_information_record.record_dict:
                dev_record[k] = v
            iter_record = json_data[tr.ResultsRecordTypeEnums.IterationRecordType]
            # append the test iteration result to the list of existing iterations.
            iter_record.append(record.test_iteration_result_record.record_dict)
            
            json_data[tr.ResultsRecordTypeEnums.SummaryRecordType] = summary_record
            json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType] = dev_record
            json_data[tr.ResultsRecordTypeEnums.IterationRecordType] = iter_record
        
        else: # if the file is empty first time
            json_data[tr.ResultsRecordTypeEnums.SummaryRecordType] = record.summary_result_record
            json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType] = record.device_information_record
            json_data[tr.ResultsRecordTypeEnums.IterationRecordType] = record.test_iteration_result_record
            
        with open(self.file_tc_summary, 'w') as f:
                 json.dump(json_data, f)