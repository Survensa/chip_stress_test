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
import gc
import traceback
import chip.clusters as Clusters

from mobly import asserts
from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main, DiscoveryFilterType
from matter_qa.library.helper_libs.exceptions import TestCaseError, BuildControllerError, IterationError
from matter_qa.library.base_test_classes.test_results_record import  TestResultEnums 

class TC_Multiadmin(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        # This Function is used to intiate the dut object
        self.dut = self.get_dut_object()
        self.dut.factory_reset_dut()
        # This variable is used to store index of the controller in the loop
        self.current_controller = 0
        try:
            self.pair_dut()
        except TestCaseError:
            self.dut.factory_reset_dut()
            asserts.fail("Failed to commission the TH1")
        
    async def check_the_no_of_controllers_are_in_range(self):
        """
        This function will check that the Number of controllers given in the int-arg controller
        is less than the supporedfabrics of the DUT by reading the supported fabric from the 
        Node operational cluster """
        if self.matter_test_config.global_test_params.get("controllers"):
            max_fabrics = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                        Clusters.OperationalCredentials.Attributes.SupportedFabrics)
            # This condition will terimate the testcase if the controllers value is greater than the SupportedFabrics
            if self.number_of_controllers >= int(max_fabrics):
                self.dut.factory_reset_dut(stop_reset=True)
                asserts.fail(f"Controller should be less than the Supported_fabrics:{max_fabrics}")
        # This condition will terimate the testcase if the controllers argument is not passed to the script
        else:
            self.dut.factory_reset_dut(stop_reset=True)
            asserts.assert_true('controllers' in self.matter_test_config.global_test_params,
                            " controllers must be included on the command line in "
                            "the --int-arg flag as controllers:<Number of controllers>")
        
    def check_commissioning_window_timeout(self):
        if 'commissioning_window_timeout' in self.matter_test_config.global_test_params:
            self.commissioning_timeout = self.matter_test_config.global_test_params["commissioning_window_timeout"]
        # This condition will assign the default value of 180 to the commissioning_window_timeout if it is not passed to the script
        else:
            logging.info("int-arg commissioning_window_timeout is missing, Hence using the default timeout value 180 for opencommissioning")
            self.commissioning_timeout = 180
        if self.commissioning_timeout in range(180,901):
            pass
        # This condition will terimate the testcase if commissioning_window_timeout is out of range
        else:
            self.dut.factory_reset_dut(stop_reset=True)
            asserts.assert_less_equal(self.commissioning_timeout, 900, 
                                    f"commissioning_window_timeout value should be less than 901 seconds")
            asserts.assert_greater_equal(self.commissioning_timeout, 180, 
                                    f"commissioning_window_timeout value should be greater than 179 seconds")
            
    def build_controller(self, controller_id_itr) -> dict:
        # This function is used to build the controllers
        try:
            unique_controller_id = controller_id_itr + ((self.current_iteration-1) * int(self.number_of_controllers))
            logging.info(f'Controller node id for controller-{controller_id_itr} in {self.current_iteration} iteration is {unique_controller_id}') 
            # This object is used to create a new empty list in CA Index
            th_certificate_authority = self.certificate_authority_manager.NewCertificateAuthority()
            th_fabric_admin = th_certificate_authority.NewFabricAdmin(vendorId=0xFFF1, fabricId=self.th1.fabricId + self.current_controller + 1)           
            dut_node_id =  self.dut_node_id + unique_controller_id
            thnodeid = self.th1.nodeId + unique_controller_id
            th = th_fabric_admin.NewController(thnodeid)
            return {"status":"success", "dev_controller_dict":{"DUT_node_id": dut_node_id ,
                    "TH_node_id": thnodeid,
                    "TH_object": th,
                    "TH_CA": th_certificate_authority,
                    "TH_Name": f"Commissioner-{unique_controller_id}"}}
        # This execption will be catched if the we unable to build the controller
        except Exception as e:
            logging.error(f"Failed to build the controller {self.current_controller}in the iteration {self.current_iteration} with error {str(e)}"
                          ,exc_info=True)
            build_result = {"status":"failed", "failure_reason":str(e)} 
            tb = traceback.format_exc()
            raise BuildControllerError(build_result, tb)
        
    async def controller_pairing(self,controller_details_dict):
        try:
            dutnodeid = controller_details_dict.get("DUT_node_id")
            logging.info('TH1 opens a commissioning window')
            opencommissioning_result_dict = await self.openCommissioningWindow()
            if opencommissioning_result_dict.get("status") == "failed":
                await self.pairing_failure(opencommissioning_result_dict.get("failure_reason"))
                return opencommissioning_result_dict
            # This object stores the info about the open commissioning window like passcode, discriminator. 
            opencommissioning_object = opencommissioning_result_dict.get("commissioning_parameters")
            #Setuppincode for the current controller
            setuppincode = opencommissioning_object.commissioningParameters.setupPinCode
            #discriminator for the current controller
            discriminator = opencommissioning_object.randomDiscriminator
            logging.info(f'TH{self.current_controller} starts the commissioning with DUT')
            th = controller_details_dict.get("TH_object")
            th.ResetTestCommissioner()
            paring_result = th.CommissionOnNetwork(
                            nodeId=dutnodeid, setupPinCode=setuppincode,
                            filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=discriminator)
            # This condition will check for the pairing results Pass/Fail
            if not paring_result.is_success:
                await self.close_commissioning_window()
                return{"status":"failed","failure_reason":str(paring_result)}
            await self.check_nodeid_is_in_fabriclist(th, dutnodeid)
            return {"status":"Success","paring_result":paring_result}
        except Exception as e:
            return{"status":"failed","failure_reason":str(e)}
        
    async def pairing_failure(self, error): 
        # This function is used to store the failure reason for the pairing the controller  
        if self.check_execution_mode() == "full_execution_mode":
            self.update_iteration_logs()
            iteration_test_result = TestResultEnums.TEST_RESULT_FAIL
        else:
            raise TestCaseError(e)

    @async_test_body
    async def test_tc_pair_unpair(self):
        self.th1 = self.default_controller
        await self.check_the_no_of_controllers_are_in_range()
        self.check_commissioning_window_timeout()
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_pair_unpair(*args,**kwargs):
            try:
                list_of_controllers = []
                # Controller which are paired will be stored in this list
                list_of_paired_controller_index = []
                for controller_id_itr in range(1, int(self.number_of_controllers)+1):
                    # This condition is used to check the build controled is completed successfully
                    try:
                        controller_build_result = self.build_controller(controller_id_itr)
                    except BuildControllerError:
                        if not self.test_config.general_configs.continue_excution_on_fail:
                            #TODO needs to update after the harsith work
                            raise TestCaseError(e)
                        continue
                    controller_details_dict = controller_build_result.get("dev_controller_dict")
                    list_of_controllers.append(controller_details_dict)
                    self.current_controller =  controller_id_itr
                    paring_result_dict = await self.controller_pairing(controller_details_dict)
                    if paring_result_dict.get("status") == "failed":
                        paring_result = paring_result_dict.get("failure_reason")
                        logging.error("Failed to Commission the controller for {} in {} iteration with th error : {}"
                                    .format(list_of_controllers.index(controller_details_dict)+1,iteration, paring_result), exc_info=True)
                        await self.pairing_failure(str(paring_result))
                        continue
                    logging.info("Successfully commissioned the {}-controller of {} iteration".format(controller_id_itr, iteration))
                    logging.info(f"current memory for iteration {self.current_iteration} = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
                    list_of_paired_controller_index.append(controller_details_dict.get("DUT_node_id"))
                await self.collect_all_basic_analytics_info(heap_usage={"node_id": self.dut_node_id,
                                                            "iteration_number": self.current_iteration,
                                                            "dev_ctrl": self.th1, "endpoint": 0})
                await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
                await self.shutdown_all_controllers(list_of_controllers,list_of_paired_controller_index)
                gc.collect()
                # This condition will check for the result of the iteration is pass/fail
                if list_of_paired_controller_index:
                    self.end_of_iteration(iteration_result = "success")
                else:
                    self.end_of_iteration(iteration_result = "failed", failure_reason = "Failed to pair atleast 1 controller")
            except Exception as e:
                logging.error(f"Iteration {self.current_iteration} is failed with the error:{str(e)}", exc_info= True)
                self.end_of_iteration(iteration_result = "failed", 
                                            failure_reason="Iteration {} is failed with error {}"
                                            .format(self.current_controller,self.current_iteration,str(e)))
        
            except Exception as e:
                #TODO fix need after harsith code
                raise IterationError(e)
            
        tc_pair_unpair(self)
        self.dut.factory_reset_dut()
        self.end_of_test()


if __name__ == "__main__":
    default_matter_test_main(testclass=TC_Multiadmin,do_not_commision_first=True)