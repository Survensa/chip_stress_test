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

    async def unpair_failed(self, iteration, unpair_res):
        await self.collect_basic_analytics_info(pairing_duration_info={"iteration_number": iteration})
        fail_reason = unpair_res.get("failed_reason")
        self.test_result["Failed_iteration_details"].update({str(iteration): fail_reason})
        self.test_result["Fail Count"]["Iteration"].append(iteration)
        logging.error(f'iteration {iteration} is failed due to {fail_reason}')
        self.test_result["Fail Count"]["Count"] += 1
        if not self.test_config.general_configs.execution_mode_full:
            self.end_of_iteration(iteration)
            # break from script as full execution is false
            logging.info(
                'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                'execution will stop here'.format(iteration))
            self.end_of_test()
            return True
        return False

    async def pairing_unsuccessful(self, iteration, pairing_result):
        await self.collect_basic_analytics_info(pairing_duration_info={"iteration_number": iteration})
        self.end_of_iteration(iteration)
        self.test_result["Failed_iteration_details"].update({str(iteration): pairing_result[1]})
        self.test_result["Fail Count"]["Iteration"].append(iteration)
        logging.error(f'iteration {iteration} is failed')
        self.test_result["Fail Count"]["Count"] += 1
        if not self.test_config.general_configs.execution_mode_full:
            logging.info(
                'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                'execution will stop here'.format(iteration))
            self.end_of_test()
            return True
        return False

    def pairing_dut(self):
        try:
            pairing_result = self.commission_device(
                kwargs={"timeout": self.test_config.general_configs.dut_connection_timeout})

        except Exception as e:
            logging.error(f'test_tc_pair_unpair: {e}')
            fail_reason = str(e)
            pairing_result = [False, fail_reason]

        return pairing_result

    @async_test_body
    async def test_tc_pair_unpair(self):
        self.dut = self.get_dut_object()
        logging.info("Entering the test function")
        await self.pre_iteration_loop()
        for iteration in range(1, self.iterations + 1):
            try:
                # here iteration_logger will be started, pairing_duration_info will be captured
                await self.start_iteration(iteration)
                pairing_result = self.pairing_dut()
                if pairing_result[0]:
                    logging.info('Device has been Commissioned starting pair-unpair operation')
                    time.sleep(2)

                    # capture heap used after pairing with device
                    await self.collect_basic_analytics_info(heap_usage={"node_id": None, "iteration_number": iteration,
                                                                        "dev_ctrl": None, "endpoint": 0})
                    unpair_res = self.unpair_dut()
                    if unpair_res.get("stats") is False:  # when pairing fails
                        stop_execution = self.unpair_failed(iteration, unpair_res)
                        if stop_execution:
                            break
                        else:
                            continue
                    await self.collect_basic_analytics_info(pairing_duration_info={"iteration_number": iteration})
                    logging.info(f'iteration {iteration} is passed and unpairing the device is successful')
                    self.test_result["Pass Count"] += 1
                else:
                    stop_execution = await self.pairing_unsuccessful(iteration, pairing_result)
                    if stop_execution:
                        break
                    else:
                        continue
                if iteration == self.iterations:
                    self.end_of_test()
                else:
                    self.end_of_iteration(iteration)
            except Exception as e:
                logging.error(f"Exception occurred in TC_Pair.py \n exception is {e}", exc_info=True)
                self.end_of_iteration(iteration)


if __name__ == "__main__":
    test_start(TC_Pair.__name__)
    default_matter_test_main(testclass=TC_Pair)
