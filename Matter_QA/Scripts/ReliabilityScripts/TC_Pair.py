#
#    Copyright (c) 2022 Project CHIP Authors
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import datetime
import logging
import os
import sys
import time

from Matter_QA.Library.HelperLibs.utils import CommissionTimeoutError, summary_log

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, default_matter_test_main


class TC_Pair(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        print("Inside TC_Pair_1 init func")

    @async_test_body
    async def test_tc_pair_unpair(self):
        self.dut = self.get_dut_object()
        logging.info("Entering the test function")
        iterations = int(self.test_config_dict["general_configs"]["iteration_number"])
        self.dut.factory_reset_dut(stop_reset=False)
        self.test_result.update({"Failed_iteration_details": {}})
        self.test_result.update({"analytics": {}})
        pairing_duration_info = {}
        for i in range(1, iterations + 1):
            logging.info("Started Iteration sequence {}".format(i))
            fail_reason = None
            self.test_config_dict["current_iteration"] = i
            self.start_iteration_logging(i, None)
            start_time = datetime.datetime.now()
            try:
                iter_result = self.commission_device(
                    kwargs={"timeout": self.test_config_dict["general_configs"]["dut_connection_timeout"]})
            except Exception as e:
                logging.error(f'test_tc_pair_unpair: {e}')
                fail_reason = str(e)
                iter_result = [False, fail_reason]
            if iter_result[0]:
                logging.info('Device has been Commissioned starting pair-unpair operation')
                time.sleep(2)
                unpair_res = self.unpair_dut()
                if unpair_res.get("stats") is False:
                    end_time = datetime.datetime.now()
                    total_pairing_time = round((end_time - start_time).total_seconds(), 4)
                    fail_reason = unpair_res.get("failed_reason")
                    pairing_duration_info.update({str(i): total_pairing_time})
                    self.test_result["Failed_iteration_details"].update({str(i): fail_reason})
                    self.test_result["Fail Count"]["Iteration"].append(i)
                    logging.error(f'iteration {i} is failed due to {fail_reason}')
                    self.test_result["Fail Count"]["Count"] += 1
                    if not self.test_config_dict["general_configs"]["execution_mode_full"]:
                        logging.info(
                            'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                            'execution will stop here'.format(i))
                        self.test_result["analytics"].update({"pairing_duration_info": pairing_duration_info})
                        summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                                    completed=True)
                        self.dut.factory_reset_dut(stop_reset=True)
                        break
                    continue
                end_time = datetime.datetime.now()
                total_pairing_time = round((end_time - start_time).total_seconds(), 4)
                pairing_duration_info.update({str(i): total_pairing_time})
                logging.info(f'iteration {i} is passed and unpairing the device is successful')
                self.test_result["Pass Count"] += 1
            else:
                end_time = datetime.datetime.now()
                total_pairing_time = round((end_time - start_time).total_seconds(), 4)
                pairing_duration_info.update({str(i): total_pairing_time})
                self.test_result["Failed_iteration_details"].update({str(i): iter_result[1]})
                self.test_result["Fail Count"]["Iteration"].append(i)
                logging.error(f'iteration {i} is failed')
                self.test_result["Fail Count"]["Count"] += 1
                if not self.test_config_dict["general_configs"]["execution_mode_full"]:
                    logging.info(
                        'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                        'execution will stop here'.format(i))
                    self.test_result["analytics"].update({"pairing_duration_info": pairing_duration_info})
                    summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                                completed=True)
                    self.dut.factory_reset_dut(stop_reset=True)
                    break
            if i == iterations:
                self.dut.factory_reset_dut(stop_reset=True)
            else:
                self.dut.factory_reset_dut(stop_reset=False)
            logging.info('completed pair and unpair sequence for {}'.format(i))
            self.test_result["analytics"].update({"pairing_duration_info": pairing_duration_info})
            summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,completed=False)
            self.stop_iteration_logging(i, None)
        self.test_result["analytics"].update({"pairing_duration_info": pairing_duration_info})
        summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                    completed=True)


if __name__ == "__main__":
    test_start(TC_Pair.__name__)
    default_matter_test_main(testclass=TC_Pair)
