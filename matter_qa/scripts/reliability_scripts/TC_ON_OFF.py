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
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main
from matter_qa.library.helper_libs.exceptions import TestCaseError, IterationError
from matter_qa.library.base_test_classes.test_results_record import TestresultsRecord, TestResultEnums
from mobly import asserts
import chip.clusters as Clusters


class TC_ON_OFF(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        # Todo move this into some meta data
        self.tc_name = "ON_OFF_SCRIPT"
        self.tc_id = "stress_1_1"
        self.dut_pair_status = False
        super().__init__(*args)

    def check_cluster_status(self, after_operation_cluster_status, current_cluster_status):
        # This function is used to check the write command is executed successfully
        if after_operation_cluster_status != current_cluster_status:
            self.iteration_test_result = TestResultEnums.TEST_RESULT_PASS
        else:
            logging.info("The iteration will be failed as there is no change in cluster state after write operation")
            self.iteration_test_result = TestResultEnums.TEST_RESULT_FAIL

    async def verify_switch_on_off_cluster(self):
        try:
            clusters = Clusters.Objects.OnOff
            # For checking the current State of On-OFF cluster
            current_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                    attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                    endpoint=1)
            # if current_cluster_status is True then cluster is in ON state else it is OFF
            logging.info(
                f"The ON-OFF cluster's current condition is {'ON' if current_cluster_status is True else 'OFF'}")

            # This condition will write the opposite value of read
            await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                      payload=Clusters.OnOff.Commands.Toggle())
            after_operation_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                            attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                            endpoint=1)

            self.check_cluster_status(after_operation_cluster_status, current_cluster_status)
        except Exception as e:
            logging.error(e, exc_info=True)
            self.iteration_test_result = TestResultEnums.TEST_RESULT_FAIL
            raise IterationError(e)

    @async_test_body
    async def test_tc_on_off(self):
        self.dut.factory_reset_dut()  # performing factory reset on DUT
        if self.pair_dut():
            logging.info("Device Has been commissioned proceeding forward with execution")
        else:
            asserts.fail("Pairing has not been done, exiting from code")

        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_on_off(*args, **kwargs):
            try:
                logging.info('starting ON - OFF  operation')
                await self.verify_switch_on_off_cluster()
                await self.fetch_analytics_from_dut()
                time.sleep(2)
            except Exception as e:
                raise TestCaseError(e)
        await tc_on_off(self)
        self.dut.factory_reset_dut()


if __name__ == "__main__":
    #TODO change later remove for all scripts the arguments 'do_not_commision_first=True'
    default_matter_test_main(testclass=TC_ON_OFF, do_not_commision_first=True)
