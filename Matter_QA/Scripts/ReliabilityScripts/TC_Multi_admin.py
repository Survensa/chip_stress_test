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
    def __init__(self, *args):
        super().__init__(*args)

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
                if fabricDescriptor.nodeID == nodeId:
                    return fabricDescriptor.fabricIndex
            return 0, False
        except Exception as e:
            logging.error(str(e))
            traceback.print_exc()
            return 0, str(e)

    async def remove_all_nodes(self, controllers):
        for controller in controllers:
            try:
                logging.info(f'controller Details {controller}')
                logging.info(f'unpairing {controller["name"]}')
                response = await self.read_single_attribute_check_success(
                    cluster=Clusters.Objects.OperationalCredentials,
                    attribute=Clusters.OperationalCredentials.Attributes.CommissionedFabrics,
                    endpoint=0)
                logging.info(f"the fabrics before unpairing are {response}")
                self.unpair_dut(controller["fabric_object"], node_id=controller["fabric_dut_node_id"])
                # fbIdx = await self._IsNodeInFabricList(controller["fabric_object"], controller["fabric_dut_node_id"])
                # logging.info(f" starting removal of fabric {fbIdx}")
                # await controller["fabric_object"].SendCommand(
                #     controller["fabric_dut_node_id"], 0,
                #     Clusters.OperationalCredentials.Commands.RemoveFabric(fabricIndex=fbIdx))
                # logging.info(f"removed fabric {fbIdx}")
                await asyncio.sleep(2)
            except Exception as e:
                logging.error(e)
                traceback.print_exc()

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

    async def on_off_dev(self, fabrics):
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
        device_info = await self.device_info()  # pulls basic cluster information this is must be present at all times
        self.test_result.update({"device_basic_information": device_info})
        self.dut = self.get_dut_object()
        self.test_result.update({"Failed_iteration_details": {}})
        pairing_duration_info = {}
        fabric_creation = {}
        used_heap = {}
        for iteration in range(1, self.test_config_dict["general_configs"]["iteration_number"] + 1):
            self.start_iteration_logging(iteration, None)
            fabrics = []
            logging.info("Started Iteration sequence {}".format(iteration))
            start_time_f = datetime.datetime.now()
            for fabric_id_itr in range(1, int(dict_args["--fabrics"])):  # here we build different fabrics/node
                fabric_details = self.build_fabrics(int(fabric_id_itr))
                await self.pair_the_nodes(fabric_details), asyncio.sleep(2)
                fabrics.append(fabric_details)
            # fabrics = await self.build_controllers(fabrics, int(dict_args["--controllers"]))
            end_time_f = datetime.datetime.now()
            controller_build_time = round((end_time_f - start_time_f).total_seconds(), 4)
            fabric_creation.update({str(iteration): controller_build_time})
            self.test_config_dict["current_iteration"] = iteration
            # start_time = datetime.datetime.now()
            # response = await self.on_off_dev(fabrics)
            # end_time = datetime.datetime.now()
            # total_pairing_time = round((end_time - start_time).total_seconds(), 4)
            # pairing_duration_info.update({str(iteration): total_pairing_time})
            heap_usage = await self.get_heap_usage()
            used_heap.update({str(iteration): heap_usage[0]})
            # if False:
            #     self.test_result["Failed_iteration_details"].update({str(iteration): str(response[1])})
            #     self.test_result["Fail Count"]["Iteration"].append(iteration)
            #     logging.error(f'iteration {iteration} is failed')
            #     self.test_result["Fail Count"]["Count"] += 1
            #     if not self.test_config_dict["general_configs"]["execution_mode_full"]:
            #         logging.info(
            #             'Full Execution mode is disabled \n The iteration {} number has failed hence the '
            #             'execution will stop here'.format(iteration))
            #         self.dut.factory_reset_dut(stop_reset=True)
            #         self.stop_iteration_logging(iteration, None)
            #         break
            #     continue
            self.test_result["Pass Count"] += 1
            logging.info(f'iteration {iteration} is passed')
            self.stop_iteration_logging(iteration, None)
            time.sleep(3)
            self.analytics_json["analytics"].update({"controller_build_time": fabric_creation})
            self.analytics_json["analytics"].update({"heap_usage": used_heap})
            # self.analytics_json["analytics"].update({"response_time_on_off": pairing_duration_info})
            summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                        completed=True, analytics_json=self.analytics_json)
            await self.remove_all_nodes(fabrics)
        self.analytics_json["analytics"].update({"controller_build_time": fabric_creation})
        self.analytics_json["analytics"].update({"heap_usage": used_heap})
        # self.analytics_json["analytics"].update({"response_time": pairing_duration_info})
        summary_log(test_result=self.test_result, test_config_dict=self.test_config_dict,
                    completed=True, analytics_json=self.analytics_json)
        self.dut.factory_reset_dut(stop_reset=True)


if __name__ == "__main__":
    dict_args = convert_args_dict(sys.argv[1:])
    if "--fabrics" not in dict_args and "--controllers" not in dict_args:
        logging.error("--fabrics <integer> and --controllers <integer> not specified in arguments!! exiting now !!")
        sys.exit(0)
    test_start(test_class_name=TC_Multi_admin.__name__)
    default_matter_test_main(testclass=TC_Multi_admin)
