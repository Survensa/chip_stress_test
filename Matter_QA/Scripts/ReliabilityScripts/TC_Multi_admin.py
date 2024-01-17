import asyncio
import datetime
import logging
import random
import sys
import time
import traceback
from typing import Any
import chip.clusters as Clusters
from chip.utils import CommissioningBuildingBlocks
from chip.clusters import OperationalCredentials as opCreds
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, \
    default_matter_test_main, DiscoveryFilterType
from Matter_QA.Library.HelperLibs.utils import convert_args_dict, summary_log


class TC_Multi_admin(MatterQABaseTestCaseClass):
    def build_fabrics(self, i: int):
        try:
            logging.info(f'node id {i}')
            fabric_certificate_authority = self.certificate_authority_manager.NewCertificateAuthority()
            th2_fabric_admin = fabric_certificate_authority.NewFabricAdmin(vendorId=0xFFF1,
                                                                           fabricId=self.th1.fabricId + i)
            fabric_dut_node = self.dut_node_id + i
            fabric_node_id = self.th1.nodeId + i
            return {"fabric_dut_node_id": fabric_dut_node,
                    "fabric_object": th2_fabric_admin.NewController(fabric_node_id),
                    "name": f"Fabric number {str(i)}"}
        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
            return [0, str(e)]

    async def pair_the_nodes(self, fabric_details):
        try:
            dut_node_id_on_fabric = fabric_details["fabric_dut_node_id"]
            logging.info('TH1 opens a commissioning window')
            pin, code = self.OpenCommissioningWindow()
            logging.info(f'{fabric_details} fully commissions the DUT')
            fabric_details.get("fabric_object").ResetTestCommissioner()
            comms_resp = fabric_details.get("fabric_object").CommissionOnNetwork(
                nodeId=dut_node_id_on_fabric, setupPinCode=pin,
                filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=self.matter_test_config.discriminators[0])
            logging.info('Commissioning complete done. Successful? {}, errorcode = {}'.format(comms_resp.is_success,
                                                                                              comms_resp.sdk_code))

            if not await self._IsNodeInFabricList(self.th1, self.dut_node_id):
                return 0, await self._IsNodeInFabricList(self.th1, self.dut_node_id)

            if not await self._IsNodeInFabricList(fabric_details.get("fabric_object"), dut_node_id_on_fabric):
                return 0, await self._IsNodeInFabricList(self.th1, self.dut_node_id)
            time.sleep(2)
            return 1, True
        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
            return [0, str(e)]

    def OpenCommissioningWindow(self) -> tuple[Any, Any]:
        try:
            result = self.th1.OpenCommissioningWindow(
                nodeid=self.dut_node_id, timeout=600, iteration=10000,
                discriminator=self.matter_test_config.discriminators[0], option=1)
            time.sleep(5)
            return result.setupPinCode, result.setupManualCode

        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
            logging.exception('Error running OpenCommissioningWindow %s', e)
            return 0, str(e)

    async def _IsNodeInFabricList(self, devCtrl, nodeId):
        try:
            resp = await devCtrl.ReadAttribute(nodeId, [(opCreds.Attributes.Fabrics)])
            listOfFabricsDescriptor = resp[0][opCreds][Clusters.OperationalCredentials.Attributes.Fabrics]
            for fabricDescriptor in listOfFabricsDescriptor:
                logging.info("Fabric Descriptor Read From the Device: ", fabricDescriptor)
                if fabricDescriptor.nodeID == nodeId:
                    return fabricDescriptor.fabricIndex
            return 0, False
        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
            return 0, str(e)

    async def remove_all_nodes(self, controllers):
        for controller in controllers:
            logging.info(f" starting removal of {controller['name']}")

            fbIdx = await self._IsNodeInFabricList(controller["fabric_object"], controller["fabric_dut_node_id"])
            await controller["fabric_object"].SendCommand(
                controller["fabric_dut_node_id"], 0,
                Clusters.OperationalCredentials.Commands.RemoveFabric(fabricIndex=fbIdx))
            logging.info(f"removed fabric {fbIdx}")
            await asyncio.sleep(2)

    async def build_controllers(self, fabrics: list, number_of_controllers):
        for fabric in fabrics:
            try:
                fbIdx = await self._IsNodeInFabricList(fabric["fabric_object"], fabric["fabric_dut_node_id"])
                controllers = await CommissioningBuildingBlocks.CreateControllersOnFabric(
                    fabric["fabric_object"].fabricAdmin,
                    fabric["fabric_object"],
                    [(fbIdx * 100) + i for i in
                     range(1, number_of_controllers)],
                    Clusters.AccessControl.Enums.
                    AccessControlEntryPrivilegeEnum.
                    kAdminister,
                    fabric["fabric_dut_node_id"])
                fabric.update({"controllers": controllers})
            except Exception as e:
                logging.error(str(e))
                traceback.print_exc()
                return 0, str(e)
        return fabrics

    async def on_off_dev(self, fabrics, ):
        try:
            fabric_random_1 = random.choice(fabrics)
            controller_random_1 = random.choice(fabric_random_1["controllers"])
            logging.info(
                f"Random fabric chosen is {fabric_random_1['name']},"
                f"random controller used for ON operation is {controller_random_1}")
            clusters = Clusters.Objects.OnOff
            on_off_stats = await self.read_single_attribute_check_success(cluster=clusters,
                                                                          attribute=Clusters.OnOff.Attributes.OnOff,
                                                                          endpoint=1)
            logging.info(f"The cluster's current condition is {'ON' if on_off_stats else 'OFF'}")
            await controller_random_1.SendCommand(nodeid=fabric_random_1["fabric_dut_node_id"], endpoint=1,
                                                  payload=Clusters.OnOff.Commands.Off())
            time.sleep(3)
            fabric_random_2 = random.choice(fabrics)
            controller_random_2 = random.choice(fabric_random_2["controllers"])
            logging.info(
                f"Random fabric chosen is {fabric_random_2['name']}, "
                f"random controller used for OFF operation is {controller_random_2}")
            await controller_random_2.SendCommand(nodeid=fabric_random_2["fabric_dut_node_id"], endpoint=1,
                                                  payload=Clusters.OnOff.Commands.Off())
            return 1, True
        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
            return 0, str(e)

    @async_test_body
    async def test_stress_test_multi_fabric(self):
        self.th1 = self.default_controller
        fabrics = []
        self.dut = self.get_dut_object()
        for i in range(1, int(dict_args["--fabrics"])):
            fabric_details = self.build_fabrics(int(i))
            await self.pair_the_nodes(fabric_details), asyncio.sleep(2)
            fabrics.append(fabric_details)
        fabrics = await self.build_controllers(fabrics, int(dict_args["--controllers"]))
        self.test_result.update({"Failed_iteration_details": {}})
        pairing_duration_info = {}
        for i in range(self.test_config_dict["general_configs"]["iteration_number"]):
            logging.info("Started Iteration sequence {}".format(i))
            self.test_config_dict["current_iteration"] = i
            self.start_iteration_logging(i, None)
            start_time = datetime.datetime.now()
            response = await self.on_off_dev(fabrics)
            end_time = datetime.datetime.now()
            total_pairing_time = round((end_time - start_time).total_seconds(), 4)
            pairing_duration_info.update({str(i): total_pairing_time})
            if 0 in response:
                self.test_result["Failed_iteration_details"].update({str(i): str(response[1])})
                self.test_result["Fail Count"]["Iteration"].append(i)
                logging.error(f'iteration {i} is failed')
                self.test_result["Fail Count"]["Count"] += 1
                if not self.test_config_dict["general_configs"]["execution_mode_full"]:
                    logging.info(
                        'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                        'execution will stop here'.format(i))
                    self.dut.factory_reset_dut(stop_reset=True)
                    break
                continue
            self.test_result["Pass Count"] += 1
            logging.info(f'iteration {i} is passed')
            time.sleep(3)
        self.test_result.update({"pairing_duration_info": pairing_duration_info})
        summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict)
        self.dut.factory_reset_dut(stop_reset=True)


if __name__ == "__main__":
    dict_args = convert_args_dict(sys.argv[1:])
    if "--fabrics" not in dict_args and "--controllers" not in dict_args:
        logging.error("--fabrics <integer> and --controllers <integer> not specified in arguments!! exiting now !!")
        sys.exit(0)
    test_start(test_class_name=TC_Multi_admin.__name__)
    default_matter_test_main(testclass=TC_Multi_admin)
