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
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.HelperLibs.matter_testing_support import CustomCommissioningParameters, async_test_body,\
                 default_matter_test_main, DiscoveryFilterType


class TC_Multi_admin(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        self.dut = self.get_dut_object()
        self.commissioning_window_startime = None
        self.current_controller = 0

    async def check_the_no_of_controllers_are_in_range(self):
        asserts.assert_true('controllers' in self.matter_test_config.global_test_params,
                            " controllers must be included on the command line in "
                            "the --int-arg flag as controllers:<Number of controllers>")
        max_fabrics = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                       Clusters.OperationalCredentials.Attributes.SupportedFabrics)
        asserts.assert_less_equal(self.number_of_controllers, int(max_fabrics)-1, 
                                  f"Controller should be less than are equal to the Supported_fabrics:{max_fabrics}")
        
    def check_the_commissioning_window_timeout(self):
        if 'commissioning_window_timeout' in self.matter_test_config.global_test_params:
            self.commissioning_timeout = self.matter_test_config.global_test_params["commissioning_window_timeout"]
        else:
            logging.info("int-arg commissioning_window_timeout is missing, Hence using the default timeout value 180 for opencommissioning")
            self.commissioning_timeout = 180
        asserts.assert_less_equal(self.commissioning_timeout, 900, 
                                  f"commissioning_window_timeout value should be less than 901 seconds")
        asserts.assert_greater_equal(self.commissioning_timeout, 180, 
                                  f"commissioning_window_timeout value should be greater than 179 seconds")

    def build_controller(self, controller_id_itr) -> dict:
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
        except Exception as e:
            logging.error(f"Failed to build the controller {self.current_controller}in the iteration {self.current_iteration} with error {str(e)}"
                          ,exc_info=True)
            return {"status":"failed", "failure_reason":str(e)} 
        
    async def openCommissioningWindow(self) -> dict:
        rnd_discriminator = random.randint(0, 4095)
        try:
            self.commissioning_window_startime = None
            commissioning_params = self.th1.OpenCommissioningWindow(nodeid=self.dut_node_id, timeout=self.commissioning_timeout, iteration=1000,
                                                                    discriminator=rnd_discriminator, option=1)
            customcommissioningparameters = CustomCommissioningParameters(commissioning_params, rnd_discriminator)
            self.commissioning_window_startime = time.time()
            return {"status":"Success","commissioning_parameters": customcommissioningparameters}

        except ChipStackError as e:
            logging.error(f"Failed to open the commissioning window :{str(e)}", exc_info=True)
            await self.pairing_failure(str(e))
            return {"status": "failed","failure_reason":str(e)}

    async def pairing_failure(self, error):  
        
        if self.check_execution_mode() == "full_execution_mode":
            self.log_iteration_test_results(iteration_result= "failed", 
                                            failure_reason=f"Controller{self.current_controller} of the Iteration {self.current_iteration} with the error {str(error)}")
        else:
            await self.collect_all_basic_analytics_info(heap_usage={"node_id": None,
                                                                            "iteration_number": self.current_iteration,
                                                                            "dev_ctrl": None, "endpoint": 0})
            await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
            self.end_of_iteration(iteration_result = "failed", failure_reason = error)
            self.dut.factory_reset_dut(stop_reset=True)
            self.end_of_test()
            asserts.fail(error, "Failed to pair the New controller")
    
    async def controller_pairing(self,controller_details_dict, iteration):
        dutNodeId = controller_details_dict.get("DUT_node_id")
        logging.info('TH1 opens a commissioning window')
        opencommissioning_result_dict = await self.openCommissioningWindow()
        if opencommissioning_result_dict.get("status") == "failed":
            self.pairing_failure(opencommissioning_result_dict.get("failure_reason"))
            return opencommissioning_result_dict
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
        if not paring_result.is_success:
            await self.close_commissioning_window()
            return{"status":"failed","failure_reason":str(paring_result)}
        await self.check_nodeid_is_in_fabriclist(th, dutNodeId)
        return {"status":"Success","paring_result":paring_result}
        
    async def check_nodeid_is_in_fabriclist(self, devCtrl, nodeId):
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
    
    async def shutdown_all_controllers(self, list_of_controllers, list_of_paired_controllers):
        for controller_details_dict in list_of_controllers:
                th = controller_details_dict.get("TH_object")
                dutNodeId = controller_details_dict.get("DUT_node_id")
                if controller_details_dict in list_of_paired_controllers:
                    logging.info("Unpairing the controller-{} of iteration {}"
                                 .format(list_of_controllers.index(controller_details_dict) , self.current_iteration))
                    unpair_result = self.unpair_dut(th, dutNodeId)
                    if unpair_result.get("status") == "failed":
                        logging.error("Failed to unpair the controller-{} in the iteration {} with the error:{}"
                                      .format(self.current_controller,self.current_iteration ,unpair_result.get("failed_reason")) 
                                      ,exc_info=True)
                        await self.unpair_failure(unpair_result.get("failed_reason"))
                th.Shutdown()
                
    async def controller_creation_failure(self, controller_details_dict):
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
        if self.check_execution_mode() == "full_execution_mode":
            self.log_iteration_test_results(iteration_result= "failed", failure_reason=str(error))
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
        if self.commissioning_window_startime == None:
            return None
        while True:
            if time.time()- self.commissioning_window_startime > self.commissioning_timeout:
                break
            try:
                revokeCmd = Clusters.AdministratorCommissioning.Commands.RevokeCommissioning()
                await self.th1.SendCommand(nodeid=self.dut_node_id, endpoint=0, payload=revokeCmd, timedRequestTimeoutMs=1000)
                time.sleep(1)
            except Exception as e:
                logging.error("Failed to close the commissioning window due to the error {}".format(e),exc_info=True)      
    
    @async_test_body
    async def test_stress_test_multi_fabric(self):
        self.number_of_controllers = self.matter_test_config.global_test_params["controllers"]
        self.check_the_commissioning_window_timeout()
        await self.check_the_no_of_controllers_are_in_range()
        self.th1 = self.default_controller
        await self.pre_iteration_loop()
        for iteration in range(1, self.iterations + 1):
            logging.info(f"intial memory for iteration {self.current_iteration} = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
            await self.start_iteration(iteration = iteration)
            list_of_controllers = []
            list_of_paired_controller = []
            for controller_id_itr in range(1, int(self.number_of_controllers)+1):
                #dut-Node-id for the current controller
                controller_build_result = self.build_controller(controller_id_itr)
                if controller_build_result.get("status") == "failed":
                    await self.controller_creation_failure(controller_details_dict)
                    continue
                controller_details_dict = controller_build_result.get("dev_controller_dict")
                list_of_controllers.append(controller_details_dict)
                self.current_controller =  controller_id_itr
                paring_result_dict = await self.controller_pairing(controller_details_dict , iteration)
                if paring_result_dict.get("status") == "failed":
                    paring_result = paring_result_dict.get("failure_reason")
                    logging.error("Failed to Commission the controller for {} in {} iteration with th error : {}"
                                  .format(list_of_controllers.index(controller_details_dict)+1,iteration, paring_result), exc_info=True)
                    await self.pairing_failure(str(paring_result))
                    continue
                logging.info("successfully commissioned the {}-controller of {} iteration".format(controller_id_itr, iteration))
                logging.info(f"current memory for iteration {self.current_iteration} = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
                list_of_paired_controller.append(controller_details_dict)
            await self.collect_all_basic_analytics_info(heap_usage={"node_id": self.dut_node_id,
                                                        "iteration_number": self.current_iteration,
                                                        "dev_ctrl": self.th1, "endpoint": 0})
            await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
            await self.shutdown_all_controllers(list_of_controllers,list_of_paired_controller)
            self.end_of_iteration(iteration_result = "success")
            logging.info(f"final memory for iteration {self.current_iteration} = {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
        self.dut.factory_reset_dut(stop_reset=True)
        self.end_of_test()

if __name__ == "__main__":
    logging.info(f"intial memory before execution {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
    test_start(test_class_name=TC_Multi_admin.__name__)
    default_matter_test_main(testclass=TC_Multi_admin)
    logging.info(f"final memory after execution {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}")
