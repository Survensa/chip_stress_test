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
import logging
from mobly import asserts
import chip.clusters as Clusters

from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main 
from matter_qa.library.helper_libs.exceptions import TestCaseError, TestCaseExit
from matter_qa.library.base_test_classes.test_results_record import TestResultEnums

class TC_Multiadmin(MatterQABaseTestCaseClass):

    def __init__(self, *args):
        #Todo move this into some meta data
        self.tc_name = "Multi_Admin"
        self.tc_id = "stress_1_2"
        super().__init__(*args)

    def create_unique_controller_id(self, fabric):
        #To create a unquie value to each controller
        return fabric + ((self.test_config.current_iteration-1) * self.max_fabric_supported_by_dut)
    
    def create_unique_node_id(self, fabric):
        #To create a unquie node_id for each controller
        return self.dut_node_id + fabric + ((self.test_config.current_iteration-1) * self.max_fabric_supported_by_dut)

    def find_dut_node_id(self, controller_index):
        return self.dut_node_id + controller_index + ((self.test_config.current_iteration-1) * self.max_fabric_supported_by_dut)+1
        
    async def create_list_of_paired_controllers (self):
        list_of_paired_controllers = []
        try:
            self.max_fabric_supported_by_dut = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                    Clusters.OperationalCredentials.Attributes.SupportedFabrics)
            # Th1 is already paired using rest of the controllers
            for fabric in range(1, self.max_fabric_supported_by_dut):
                unique_controller_id = self.create_unique_controller_id(fabric)
                controller_object = self.build_controller_object(unique_controller_id)
                open_commissioning_window_parameters = self.openCommissioningWindow(dev_ctrl = self.default_controller, node_id = self.dut_node_id)
                unique_node_id = self.create_unique_node_id(fabric)
                await self.pair_new_controller_with_dut(controller_object, unique_node_id ,open_commissioning_window_parameters)
                list_of_paired_controllers.append(controller_object)
        except Exception as e:
            self.iteration_test_result == TestResultEnums.TEST_RESULT_FAIL
        return list_of_paired_controllers
        
    def decommission_the_paired_controller(self, list_of_paired_controllers):
        try: 
            for controller_object in list_of_paired_controllers:
                dut_node_id = self.find_dut_node_id(list_of_paired_controllers.index(controller_object))
                self.unpair_dut(controller_object,dut_node_id)
                controller_object.Shutdown()
        except Exception as e:
            # When the unpairing of 1 controller is failed all the upcomming iteration will be failed 
            # Hence terminating the testcase using TestCaseExit Exception
            logging.error("Failed to unpair the controller{}".format(e), exc_info=True)
            raise TestCaseExit(str(e))

    @async_test_body
    async def test_tc_multi_admin(self):
        self.dut.factory_reset_dut()
        if self.pair_dut():
            logging.info("Device Has been commissioned proceeding forward with execution")
        else:
            asserts.fail("Pairing has not been done, exiting from code")
            
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_multi_admin(*args,**kwargs):
            #List contains the controller object
            list_of_paired_controllers = await self.create_list_of_paired_controllers()
            self.decommission_the_paired_controller(list_of_paired_controllers)
            self.iteration_test_result = TestResultEnums.TEST_RESULT_PASS
            await self.fetch_analytics_from_dut()
                
        await tc_multi_admin(self)
        
if __name__ == "__main__":
    default_matter_test_main(testclass=TC_Multiadmin,do_not_commision_first = True)