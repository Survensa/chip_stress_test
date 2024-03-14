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
import random
import time
import chip.clusters as Clusters
from chip.exceptions import ChipStackError
from chip.interaction_model import InteractionModelError
from mobly import asserts
import sys
import os
import resource
from chip.clusters import OperationalCredentials as opCreds
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))
import gc
from Matter_QA.Library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.helper_libs.matter_testing_support import CustomCommissioningParameters, async_test_body,\
                 default_matter_test_main, DiscoveryFilterType


class TC_Multi_admin(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        self.dut = self.get_dut_object()
        # This variable store the Start-time of the Open commissioning window 
        self.commissioning_window_start_time = None
        self.current_controller = 0

    async def check_the_no_of_controllers_are_in_range(self):
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
        
    def check_the_commissioning_window_timeout(self):
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
            th_certificate_authority = self.certificate_authority_manager.NewCertificateAuthority()
            th_fabric_admin = th_certificate_authority.NewFabricAdmin(vendorId=0xFFF1, fabricId=self.th1.fabricId + unique_controller_id)
            dut_node_id =  self.dut_node_id + unique_controller_id
            thNodeId = self.th1.nodeId + unique_controller_id
            th = th_fabric_admin.NewController(thNodeId)
            return {"status":"success", "dev_controller_dict":{"DUT_node_id": dut_node_id ,
                    "TH_node_id": thNodeId,
                    "TH_object": th,
                    "TH_Name": f"Commissioner-{unique_controller_id}"}}
        # This execption will be catched if the we unable to build the controller
        except Exception as e:
            logging.error(f"Failed to build the controller {self.current_controller}in the iteration {self.current_iteration} with error {str(e)}"
                          ,exc_info=True)
            return {"status":"failed", "failure_reason":str(e)} 
        
    async def openCommissioningWindow(self) -> dict:
        # This function is used to OPen the commisioning window
        rnd_discriminator = random.randint(0, 4095)
        try:
            self.commissioning_window_start_time = None
            commissioning_params = self.th1.OpenCommissioningWindow(nodeid=self.dut_node_id, timeout=self.commissioning_timeout, iteration=1000,
                                                                    discriminator=rnd_discriminator, option=1)
            customcommissioningparameters = CustomCommissioningParameters(commissioning_params, rnd_discriminator)
            self.commissioning_window_start_time = time.time()
            return {"status":"Success","commissioning_parameters": customcommissioningparameters}

        except ChipStackError as e:
            logging.error(f"Failed to open the commissioning window :{str(e)}", exc_info=True)
            await self.pairing_failure(str(e))
            return {"status": "failed","failure_reason":str(e)}

    async def pairing_failure(self, error): 
        # This function is used to store the failure reason for the pairing the controller  
        if self.check_execution_mode() == "full_execution_mode":
            self.log_iteration_test_results(iteration_result= "failed", 
                                            failure_reason=f"Failed to pair the Controller{self.current_controller} of the Iteration {self.current_iteration} with the error {str(error)}")
        else:
            await self.collect_all_basic_analytics_info(heap_usage={"node_id": None,
                                                                            "iteration_number": self.current_iteration,
                                                                            "dev_ctrl": None, "endpoint": 0})
            await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
            self.end_of_iteration(iteration_result = "failed", failure_reason = error)
            self.dut.factory_reset_dut(stop_reset=True)
            self.end_of_test()
            asserts.fail(error, "Failed to pair the New controller")
    
    async def controller_pairing(self,controller_details_dict):
        try:
            dutNodeId = controller_details_dict.get("DUT_node_id")
            logging.info('TH1 opens a commissioning window')
            opencommissioning_result_dict = await self.openCommissioningWindow()
            if opencommissioning_result_dict.get("status") == "failed":
                self.pairing_failure(opencommissioning_result_dict.get("failure_reason"))
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
                            nodeId=dutNodeId, setupPinCode=setuppincode,
                            filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=discriminator)
            # This condition will check for the pairing results Pass/Fail
            if not paring_result.is_success:
                await self.close_commissioning_window()
                return{"status":"failed","failure_reason":str(paring_result)}
            await self.check_nodeid_is_in_fabriclist(th, dutNodeId)
            return {"status":"Success","paring_result":paring_result}
        except Exception as e:
            return{"status":"failed","failure_reason":str(e)}
            
        
    async def check_nodeid_is_in_fabriclist(self, devCtrl, nodeId):
        # This function will check for the fabric is available in the fabric-list
        try:
            resp = await devCtrl.ReadAttribute(nodeId, [(opCreds.Attributes.Fabrics)])
            listOfFabricsDescriptor = resp[0][opCreds][Clusters.OperationalCredentials.Attributes.Fabrics]
            for fabricDescriptor in listOfFabricsDescriptor:
                print("Fabric Descriptor Read From the Device: ", fabricDescriptor)
                if fabricDescriptor.nodeID == nodeId:
                    return fabricDescriptor.fabricIndex
                else:
                    self.pairing_failure()
        except Exception as e:
            logging.error("Failed to read the listOfFabricsDescriptor", exc_info=True)
            return 0
    
    async def shutdown_all_controllers(self, list_of_controllers, list_of_paired_controller_index):
        # This function will unpair the paired controller and shutdown all the controllers that created in an iteration
        for controller_details_dict in list_of_controllers:
                self.current_controller = list_of_controllers.index(controller_details_dict) +1
                th = controller_details_dict.get("TH_object")
                dutNodeId = controller_details_dict.get("DUT_node_id")
                # This condtion is used to confirm that the controller is paired to the DUT
                if dutNodeId in list_of_paired_controller_index:
                    logging.info("Unpairing the controller-{} of iteration {}"
                                 .format(self.current_controller, self.current_iteration))
                    unpair_result = self.unpair_dut(th, dutNodeId)
                    # this condition is used to check that the unpair is completed successfully
                    if unpair_result.get("status") == "failed":
                        logging.error("Failed to unpair the controller-{} in the iteration {} with the error:{}"
                                      .format(self.current_controller,self.current_iteration ,unpair_result.get("failed_reason")) 
                                      ,exc_info=True)
                        await self.unpair_failure(unpair_result.get("failed_reason"))
                try:
                    # This function is used to shutdown the controller object
                    th.Shutdown()
                except Exception as e:
                    logging.error(f"Failed to shutdown the controller-{self.current_controller} of the iterartion {self.current_iteration} with error:{str(e)}",
                                  exc_info= True)
                
    async def controller_creation_failure(self, controller_details_dict):
         # This function is used to store the failure reason for the build controller 
        if self.check_execution_mode() == "full_execution_mode":
            logging.error(f"Failed to create a Controller with the error : {controller_details_dict.get('failure_reason')}" ,exc_info=True)
        else:
            await self.collect_all_basic_analytics_info(heap_usage={"node_id": None,
                                                        "iteration_number": self.current_iteration,
                                                        "dev_ctrl": None, "endpoint": 0})
            await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
            self.end_of_iteration(iteration_result = "failed", failure_reason = controller_details_dict.get("failure_reason"))
            self.dut.factory_reset_dut(stop_reset=True)
            self.end_of_test()
            asserts.fail(controller_details_dict.get("failure_reason"), "Failed to create new controller")

    async def unpair_failure(self, error):
        #  This function is used to store the failure reason for the Unpairing the controller 
        if self.check_execution_mode() == "full_execution_mode":
            self.log_iteration_test_results(iteration_result= "failed", 
                                            failure_reason="Failed to unpair the controller-{} of iteration {}with error {}"
                                            .format(self.current_controller,self.current_iteration,str(error)))
        else:
            await self.collect_all_basic_analytics_info(heap_usage={"node_id": None,
                                                                            "iteration_number": self.current_iteration,
                                                                            "dev_ctrl": None, "endpoint": 0})
            await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
            self.end_of_iteration(iteration_result = "failed", failure_reason = str(error))
            self.dut.factory_reset_dut(stop_reset=True)
            self.end_of_test()
            asserts.fail(str(error), "Failed to unpair the controller")

    async def close_commissioning_window(self):
        # This function is used to close the commissioning window if it is open state
        if self.commissioning_window_start_time == None:
            return None
        # This loop is to confirm that the commissioning window is closed 
        while True:
            # This condtion used to break loop if the commissioning window time is reached
            if time.time()- self.commissioning_window_start_time > self.commissioning_timeout:
                break
            try:
                revokeCmd = Clusters.AdministratorCommissioning.Commands.RevokeCommissioning()
                await self.th1.SendCommand(nodeid=self.dut_node_id, endpoint=0, payload=revokeCmd, timedRequestTimeoutMs=1000)
                time.sleep(1)
            except Exception as e:
                logging.error("Failed to close the commissioning window due to the error {}".format(e),exc_info=True)      
    
    @async_test_body
    async def test_stress_test_multi_fabric(self):
        self.number_of_controllers = self.matter_test_config.global_test_params.get("controllers")
        self.check_the_commissioning_window_timeout()
        await self.check_the_no_of_controllers_are_in_range()
        self.th1 = self.default_controller
        await self.pre_iteration_loop()
        for iteration in range(1, self.iterations + 1):
            try:
                logging.info(f"intial memory for iteration {self.current_iteration} = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
                await self.start_iteration(iteration = iteration)
                # All the controller object created wiol be stored in this list
                list_of_controllers = []
                # Controller which are paired will be stored in this list
                list_of_paired_controller_index = []
                for controller_id_itr in range(1, int(self.number_of_controllers)+1):
                    controller_build_result = self.build_controller(controller_id_itr)
                    # This condition is used to check the build controled is completed successfully
                    if controller_build_result.get("status") == "failed":
                        await self.controller_creation_failure(controller_details_dict)
                        continue
                    controller_details_dict = controller_build_result.get("dev_controller_dict")
                    list_of_controllers.append(controller_details_dict)
                    # This variable is used to store index of the controller in the loop
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
                logging.info(f"Memory used for iteration {self.current_iteration} before garabe-collect = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
                gc.collect()
                logging.info(f"Memory used for iteration {self.current_iteration} after garabe-collect = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
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
        self.dut.factory_reset_dut(stop_reset=True)
        self.end_of_test()

if __name__ == "__main__":
    logging.info(f"intial memory before execution {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
    test_start(test_class_name=TC_Multi_admin.__name__)
    default_matter_test_main(testclass=TC_Multi_admin)
    logging.info(f"final memory after execution {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
