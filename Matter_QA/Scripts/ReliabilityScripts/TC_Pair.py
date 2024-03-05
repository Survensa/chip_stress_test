#
#
#  Copyright (c) 2023 Project CHIP Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
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
        device_info = await self.device_info()  # pulls basic cluster information this is must be present at all times
        self.test_result.update({"device_basic_information": device_info})
        self.dut.factory_reset_dut(stop_reset=False)
        self.test_result.update({"Failed_iteration_details": {}})
        used_heap = {}
        pairing_duration_info = {}
        for iteration in range(1, iterations + 1):
            logging.info("Started Iteration sequence {}".format(iteration))
            fail_reason = None
            self.test_config_dict["current_iteration"] = iteration
            self.start_iteration_logging(iteration, None)
            await self.capture_start_parameters(pairing_duration=pairing_duration_info)  # start to capture pairing info
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
                await self.capture_start_parameters(iteration_number=iteration, heap_usage=used_heap)  # capture heap used after pairing with device
                unpair_res = self.unpair_dut()
                if unpair_res.get("stats") is False:  # when pairing fails
                    self.capture_end_parameters(iteration, pairing_duration=pairing_duration_info)
                    fail_reason = unpair_res.get("failed_reason")
                    self.test_result["Failed_iteration_details"].update({str(iteration): fail_reason})
                    self.test_result["Fail Count"]["Iteration"].append(iteration)
                    logging.error(f'iteration {iteration} is failed due to {fail_reason}')
                    self.test_result["Fail Count"]["Count"] += 1
                    if not self.test_config_dict["general_configs"]["execution_mode_full"]:
                        # break from script as full execution is false
                        logging.info(
                            'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                            'execution will stop here'.format(iteration))
                        self.update_analytics_json(self.test_config_dict["general_configs"]["analytics_parameters"],
                                                   [pairing_duration_info,used_heap])
                        summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                                    completed=True, analytics_json=self.analytics_json)
                        self.dut.factory_reset_dut(stop_reset=True)
                        break
                    continue
                self.capture_end_parameters(iteration, pairing_duration=pairing_duration_info)
                self.update_analytics_json(self.test_config_dict["general_configs"]["analytics_parameters"],
                                           [pairing_duration_info, used_heap])
                logging.info(f'iteration {iteration} is passed and unpairing the device is successful')
                self.test_result["Pass Count"] += 1
            else:
                self.capture_end_parameters(iteration, pairing_duration=pairing_duration_info)
                self.test_result["Failed_iteration_details"].update({str(iteration): iter_result[1]})
                self.test_result["Fail Count"]["Iteration"].append(iteration)
                logging.error(f'iteration {iteration} is failed')
                self.test_result["Fail Count"]["Count"] += 1
                if not self.test_config_dict["general_configs"]["execution_mode_full"]:
                    logging.info(
                        'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                        'execution will stop here'.format(iteration))
                    self.update_analytics_json(["pairing_duration_info"],
                                               [pairing_duration_info])
                    summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                                completed=True, analytics_json=self.analytics_json)
                    self.dut.factory_reset_dut(stop_reset=True)
                    break
            if iteration == iterations:
                self.dut.factory_reset_dut(stop_reset=True)
            else:
                self.dut.factory_reset_dut(stop_reset=False)
            logging.info('completed pair and unpair sequence for {}'.format(iteration))
            self.analytics_json["analytics"].update({"pairing_duration_info": pairing_duration_info})
            summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                        completed=False, analytics_json=self.analytics_json)
            self.stop_iteration_logging(iteration, None)
        self.analytics_json["analytics"].update({"pairing_duration_info": pairing_duration_info})
        summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                    completed=True, analytics_json=self.analytics_json)


if __name__ == "__main__":
    test_start(TC_Pair.__name__)
    default_matter_test_main(testclass=TC_Pair)
