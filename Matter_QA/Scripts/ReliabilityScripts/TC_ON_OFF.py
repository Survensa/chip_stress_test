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

    async def pairing_or_unpairing_unsuccessful(self, pairing_or_pairing_result):
        await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
        self.iterations_failure_reason = f' iteration {self.current_iteration} failed because of {pairing_or_pairing_result.get("failed_reason")}'
        self.end_of_iteration(iteration_result="failed",
                              failure_reason=self.iterations_failure_reason)
        self.dut.factory_reset_dut(stop_reset=False)

    def pairing_dut(self) -> dict:
        try:
            pairing_result = self.commission_device(
                kwargs={"timeout": self.test_config.general_configs.dut_connection_timeout})
        except Exception as e:
            logging.error(f'test_tc_pair_unpair: {e}')
            pairing_result = {"status": "failed", "failed_reason": str(e)}
        return pairing_result

    @async_test_body
    async def test_tc_pair_unpair(self):
        self.dut = self.get_dut_object()
        await self.pre_iteration_loop()
        self.dut.factory_reset_dut(stop_reset=False)
        for iteration in range(1, self.iterations + 1):
            try:
                # here iteration_logger will be started, pairing_duration_info will be captured
                await self.start_iteration(iteration)
                pairing_result = self.pairing_dut()  # pairing operation with DUT begins.
                if pairing_result["status"] == "success":  # when DUT pairing has successfully occurred
                    logging.info('Device has been Commissioned starting pair-unpair operation')
                    time.sleep(2)
                    await self.on_off_dut()

                    # capture heap used after pairing with device
                    await self.collect_all_basic_analytics_info(heap_usage={"node_id": None,
                                                                            "iteration_number": self.current_iteration,
                                                                            "dev_ctrl": None, "endpoint": 0})
                    unpair_result = self.unpair_dut()  # unpair with commissioned the DUT
                    if unpair_result.get("status") == "failed":  # when unpairing from DUT Fails
                        await self.pairing_or_unpairing_unsuccessful(unpair_result)
                        if self.check_execution_mode() == "full_execution_mode":
                            continue
                        else:
                            break
                    await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
                    logging.info(f'iteration {self.current_iteration} is passed and unpairing the device is successful')

                else:  # this condition is triggered when pairing is un_successful
                    await self.pairing_or_unpairing_unsuccessful(pairing_result)
                    if self.check_execution_mode() == "full_execution_mode":
                        continue
                    else:
                        break
            except Exception as e:
                logging.error(f"Exception occurred in TC_Pair.py \n exception is {e}", exc_info=True)
                self.end_of_iteration(iteration_result="failed",
                                      failure_reason=f"exception in  TC_Pair.py {str(e)}")
                self.dut.factory_reset_dut(stop_reset=False)
                continue
            self.dut.factory_reset_dut(stop_reset=False)
            self.end_of_iteration(iteration_result="success")
        self.dut.factory_reset_dut(stop_reset=True)
        self.end_of_test()



if __name__ == "__main__":
    test_start(TC_Pair.__name__)
    default_matter_test_main(testclass=TC_Pair)
