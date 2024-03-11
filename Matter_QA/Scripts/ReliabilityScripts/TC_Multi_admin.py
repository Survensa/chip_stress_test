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
import random
import time
import traceback
from chip import ChipDeviceCtrl
import chip.clusters as Clusters
from chip.interaction_model import InteractionModelError
from mobly import asserts
from chip.clusters import OperationalCredentials as opCreds
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.HelperLibs.matter_testing_support import CustomCommissioningParameters, async_test_body,\
                 default_matter_test_main, DiscoveryFilterType
from Matter_QA.Library.HelperLibs.utils import  summary_log


class TC_Multi_admin(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        self.dut = self.get_dut_object()
        self.unique_node_id = 0

    async def check_the_no_of_controllers_are_in_range(self):
        asserts.assert_true('controllers' in self.matter_test_config.global_test_params,
                            " controllers must be included on the command line in "
                            "the --int-arg flag as controllers:<Number of controllers>")
        max_fabrics = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                       Clusters.OperationalCredentials.Attributes.SupportedFabrics)
        asserts.assert_less_equal(self.number_of_controllers, int(max_fabrics)-1, f"Controller should be less than are equal to the Supported_fabrics:{max_fabrics}")

    def build_controller(self, controller_id_itr) -> dict:
        try:
            controller_node_id = controller_id_itr + (self.unique_node_id * int(self.number_of_controllers))
            logging.info(f'Controller node id {controller_node_id}')
            th_certificate_authority = self.certificate_authority_manager.NewCertificateAuthority()
            th_fabric_admin = th_certificate_authority.NewFabricAdmin(vendorId=0xFFF1, fabricId=self.th1.fabricId + controller_node_id)
            dut_node_id =  self.dut_node_id + controller_node_id
            thNodeId = self.th1.nodeId + controller_node_id
            th = th_fabric_admin.NewController(thNodeId)
            return {"status":"success", "dev_controller_dict":{"DUT_node_id": dut_node_id ,
                    "TH_node_id": thNodeId,
                    "TH_object": th,
                    "TH_Name": f"Commissioner-{controller_node_id}"}}
        except Exception as e:
            logging.error(str(e),exc_info=True)
            return {"status":"failed", "failure_reason":str(e)} 
        
    async def openCommissioningWindow(self) -> dict:
        rnd_discriminator = random.randint(0, 4095)
        try:
            commissioning_params = self.th1.OpenCommissioningWindow(nodeid=self.dut_node_id, timeout=900, iteration=1000,
                                                                    discriminator=rnd_discriminator, option=1)
            customcommissioningparameters = CustomCommissioningParameters(commissioning_params, rnd_discriminator)
            return {"status":"Success","commissioning_parameters": customcommissioningparameters}

        except InteractionModelError as e:
            logging.error(f"Failed to open the commissioning window :{str(e)}")
            await self.pairing_failure(str(e))
            return {"status": "failed","failure_reason":str(e)}

    async def pairing_failure(self, error):  
        await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
        self.end_of_iteration(iteration_result = "failed", failure_reason = error)
        if self.check_execution_mode() == "full_execution_mode":
            pass
        else:
            self.dut.factory_reset_dut(stop_reset=True)
            self.end_of_test()
            asserts.fail(error, "Failed to pair the New controller")
    
    def controller_pairing(self, th, dutNodeId, setuppincode, discriminator):
        th.ResetTestCommissioner()
        paring_result = th.CommissionOnNetwork(
                        nodeId=dutNodeId, setupPinCode=setuppincode,
                        filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=discriminator)
        return paring_result
        
    async def check_nodeid_is_in_fabriclist(self, devCtrl, nodeId):
        resp = await devCtrl.ReadAttribute(nodeId, [(opCreds.Attributes.Fabrics)])
        listOfFabricsDescriptor = resp[0][opCreds][Clusters.OperationalCredentials.Attributes.Fabrics]
        for fabricDescriptor in listOfFabricsDescriptor:
            print("Fabric Descriptor Read From the Device: ", fabricDescriptor)
            if fabricDescriptor.nodeID == nodeId:
                return fabricDescriptor.fabricIndex
        return 0
    
    def shutdown_all_controllers(self, list_of_controllers, list_of_paired_controllers):
        for controller_details_dict in list_of_controllers:
                th = controller_details_dict.get("TH_object")
                dutNodeId = controller_details_dict.get("DUT_node_id")
                if controller_details_dict in list_of_paired_controllers:
                    unpair = self.unpair_dut(th, dutNodeId)
                th.Shutdown()
                
                
    async def controller_creation_failure(self, controller_details_dict):
        if self.check_execution_mode() == "full_execution_mode":
            logging.error(f"Failed to create a Controller with the error : {controller_details_dict.get('failure_reason')}")
            pass
        else:
            await self.collect_all_basic_analytics_info(pairing_duration_info={"iteration_number": self.current_iteration})
            self.end_of_iteration(iteration_result = "failed", failure_reason = controller_details_dict.get("failure_reason"))
            self.dut.factory_reset_dut(stop_reset=True)
            self.end_of_test()
            asserts.fail(controller_details_dict.get("failure_reason"), "Failed to create new controller")

    @async_test_body
    async def test_stress_test_multi_fabric(self):
        self.number_of_controllers = self.matter_test_config.global_test_params["controllers"]
        await self.check_the_no_of_controllers_are_in_range()
        self.th1 = self.default_controller
        await self.pre_iteration_loop()
        for iteration in range(1, self.iterations + 1):
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
                dutNodeId = controller_details_dict.get("DUT_node_id")
                logging.info('TH1 opens a commissioning window')
                opencommissioning_result_dict = await self.openCommissioningWindow()
                if opencommissioning_result_dict.get("status") == "failed":
                    self.pairing_failure(opencommissioning_result_dict.get("failure_reason"))
                    continue
                opencommissioning_object = opencommissioning_result_dict.get("commissioning_parameters")
                #Setuppincode for the current controller
                setuppincode = opencommissioning_object.commissioningParameters.setupPinCode
                #discriminator for the current controller
                discriminator = opencommissioning_object.randomDiscriminator
                logging.info(f'TH{int(iteration)} starts the commissioning with DUT')
                th = controller_details_dict.get("TH_object")
                paring_result = self.controller_pairing(th, dutNodeId, setuppincode, discriminator)
                logging.info('Commissioning complete done. Successful? {}, errorcode = {}'.format(paring_result.is_success, paring_result))
                if not paring_result.is_success:
                    logging.error("Failed to Commission the controller for {} in {} iteration with th error : {}".format(list_of_controllers.index(controller_details_dict),iteration, paring_result))
                    await self.pairing_failure(str(paring_result))
                    revokeCmd = Clusters.AdministratorCommissioning.Commands.RevokeCommissioning()
                    await self.th1.SendCommand(nodeid=self.dut_node_id, endpoint=0, payload=revokeCmd, timedRequestTimeoutMs=1000)
                    time.sleep(1)
                    continue
                await self.check_nodeid_is_in_fabriclist(th, dutNodeId)
                list_of_paired_controller.append(controller_details_dict)
            self.shutdown_all_controllers(list_of_controllers,list_of_paired_controller)
            self.unique_node_id += 1
            self.end_of_iteration(iteration_result = "success")
        self.dut.factory_reset_dut(stop_reset=True)
        self.end_of_test()

if __name__ == "__main__":
    test_start(test_class_name=TC_Multi_admin.__name__)
    default_matter_test_main(testclass=TC_Multi_admin)
