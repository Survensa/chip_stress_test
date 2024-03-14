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
import chip.clusters as Clusters

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))
from Matter_QA.Library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main


class TC_ON_OFF(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)

    def check_cluster_status(self, after_operation_cluster_status, current_cluster_status) -> dict:
        if after_operation_cluster_status != current_cluster_status:
            return {"status": "success"}
        else:
            logging.info("The iteration will be failed as there is no change in cluster state after write operation")
            return {"status": "failed", "failure_reason": " No change in cluster state after write operation"}

    async def on_off_cluster_operations(self) -> dict:
        try:
            clusters = Clusters.Objects.OnOff
            current_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                    attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                    endpoint=1)
            # if current_cluster_status is True then cluster is in ON state else it is OFF
            logging.info(
                f"The ON-OFF cluster's current condition is {'ON' if current_cluster_status is True else 'OFF'}")
            if current_cluster_status is True:
                await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                          payload=Clusters.OnOff.Commands.Off())
                after_operation_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                                attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                                endpoint=1)
            else:
                await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                          payload=Clusters.OnOff.Commands.On())
                after_operation_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                                attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                                endpoint=1)
            return self.check_cluster_status(after_operation_cluster_status, current_cluster_status)
        except Exception as e:
            logging.error(e, exc_info=True)
            return {"status": "failed", "failure_reason": str(e)}

    @async_test_body
    async def test_tc_on_off_cluster_operation(self):
        self.dut = self.get_dut_object()
        await self.pre_iteration_loop()
        for iteration in range(1, self.iterations + 1):
            try:
                await self.start_iteration(iteration)
                operation_result = await self.on_off_cluster_operations()
                await self.collect_all_basic_analytics_info(heap_usage={"node_id": None,
                                                                        "iteration_number": self.current_iteration,
                                                                        "dev_ctrl": None, "endpoint": 0},
                                                            pairing_duration_info={
                                                                "iteration_number": self.current_iteration})
                time.sleep(1)
                if operation_result.get("status") == "failed":  # when the cluster operation fails
                    if self.check_execution_mode() == "full_execution_mode":
                        logging.info(f'iteration {self.current_iteration} is Failed')
                        self.end_of_iteration(iteration_result=operation_result.get("status"),
                                              failure_reason=operation_result.get("failure_reason"))
                        continue
                    else:
                        logging.info(
                            f'iteration {self.current_iteration} is Failed, full execution disabled completing test')
                        self.end_of_iteration(iteration_result=operation_result.get("status"),
                                              failure_reason=operation_result.get("failure_reason"))
                        break
                logging.info(f'iteration {self.current_iteration} is passed')
                self.end_of_iteration(iteration_result=operation_result.get("status"))
            except Exception as e:
                logging.error(f"Exception occurred in TC_ON_OFF.py \n exception is {e}", exc_info=True)
                self.end_of_iteration(iteration_result="failed",
                                      failure_reason=f"exception in  TC_ON_OFF.py {str(e)}")
        self.dut.factory_reset_dut(stop_reset=True)
        self.end_of_test()


if __name__ == "__main__":
    test_start(TC_ON_OFF.__name__)
    default_matter_test_main(testclass=TC_ON_OFF)
