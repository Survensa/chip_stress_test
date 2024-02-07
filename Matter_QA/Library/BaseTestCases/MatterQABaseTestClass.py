import datetime
import logging
import os
import secrets
import sys
import time
import traceback
import typing

import chip.clusters as Clusters
from typing import Any, Tuple

import yaml
from chip import ChipDeviceCtrl

from Matter_QA.Library.HelperLibs.matter_testing_support import MatterBaseTest
from Matter_QA.Library.HelperLibs.utils import (timer, convert_args_dict, dut_object_loader, yaml_config_reader,
                                                default_config_reader)

dut_objects_list = []


class MatterQABaseTestCaseClass(MatterBaseTest):
    test_config_dict = {}

    def __init__(self, *args):
        super().__init__(*args)
        self.logger = logging.getLogger('')
        self.logger.setLevel(logging.DEBUG)  # Set the logger's level
        self.test_config_dict = MatterQABaseTestCaseClass.test_config_dict
        self.dut = None
        self.__misc__init()

    def get_dut_object(self):
        global dut_objects_list
        if len(dut_objects_list) > 0:
            return dut_objects_list[0]
        else:
            logging.error("Dut object is not initialized")
            # sys.exit(0)
        # self.create_dut_object()

    def __misc__init(self):
        self.th1 = None
        self.test_result = {'Pass Count': 0, 'Fail Count': {'Count': 0, 'Iteration': []}, 'Error Count': 0}
        self.analytics_json = {"analytics": {}, "test_case_name": "", "iteration_id": ""}

    @timer
    def commission_device(self, *args, **kwargs):
        conf = self.matter_test_config
        for commission_idx, node_id in enumerate(conf.dut_node_ids):
            try:
                logging.info("Starting commissioning for root index %d, fabric ID 0x%016X, node ID 0x%016X" %
                             (conf.root_of_trust_index, conf.fabric_id, node_id))
                logging.info("Commissioning method: %s" % conf.commissioning_method)
                commission_response = self._commission_device(commission_idx)
                if commission_response[0]:
                    return commission_response
                else:
                    return [False, str(commission_response[1])]
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                return [False, str(e)]

    def _commission_device(self, i):
        try:
            dev_ctrl = self.default_controller
            conf = self.matter_test_config
            random_nodeid = secrets.randbelow(2 ** 32)
            conf.dut_node_ids = [random_nodeid]
            DiscoveryFilterType = ChipDeviceCtrl.DiscoveryFilterType
            if conf.commissioning_method == "on-network":
                return [dev_ctrl.CommissionOnNetwork(
                    nodeId=conf.dut_node_ids[i],
                    setupPinCode=conf.setup_passcodes[i],
                    filterType=DiscoveryFilterType.LONG_DISCRIMINATOR,
                    filter=conf.discriminators[i]
                )]
            elif conf.commissioning_method == "ble-wifi":
                return [dev_ctrl.CommissionWiFi(
                    conf.discriminators[i],
                    conf.setup_passcodes[i],
                    conf.dut_node_ids[i],
                    conf.wifi_ssid,
                    conf.wifi_passphrase
                )]
            elif conf.commissioning_method == "ble-thread":
                return [dev_ctrl.CommissionThread(
                    conf.discriminators[i],
                    conf.setup_passcodes[i],
                    conf.dut_node_ids[i],
                    conf.thread_operational_dataset
                )]
            elif conf.commissioning_method == "on-network-ip":
                logging.warning("==== USING A DIRECT IP COMMISSIONING METHOD NOT SUPPORTED IN THE LONG TERM ====")
                return [dev_ctrl.CommissionIP(
                    ipaddr=conf.commissionee_ip_address_just_for_testing,
                    setupPinCode=conf.setup_passcodes[i], nodeid=conf.dut_node_ids[i]
                )]
            else:
                logging.error("Invalid commissioning method %s!" % conf.commissioning_method)
                raise ValueError("Invalid commissioning method %s!" % conf.commissioning_method)
        except Exception as e:
            logging.error(f"MatterQABaseTestCaseClass.py:_commission_device: {e}")
            traceback.print_exc()
            return [False, str(e)]

    def unpair_dut(self) -> dict:
        try:
            self.th1 = self.default_controller
            self.th1.UnpairDevice(self.dut_node_id)
            time.sleep(3)
            self.th1.ExpireSessions(self.dut_node_id)
            time.sleep(3)
            return {"stats": True}
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            return {"stats": False, "failed_reason": str(e)}

    async def on_off_dut(self):
        try:
            clusters = Clusters.Objects.OnOff
            on_off_stats = await self.read_single_attribute_check_success(cluster=clusters,
                                                                          attribute=Clusters.OnOff.Attributes.OnOff,
                                                                          endpoint=1)
            logging.info(f"The cluster's current condition is {'ON' if on_off_stats else 'OFF'}")
            await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                      payload=Clusters.OnOff.Commands.On())
            on_off_stats = await self.read_single_attribute_check_success(cluster=clusters,
                                                                          attribute=Clusters.OnOff.Attributes.OnOff,
                                                                          endpoint=1)
            logging.info(f"After sending 'On' command state is  {'ON' if on_off_stats else 'OFF'}")
            await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                      payload=Clusters.OnOff.Commands.Off())
            on_off_stats = await self.read_single_attribute_check_success(cluster=clusters,
                                                                          attribute=Clusters.OnOff.Attributes.OnOff,
                                                                          endpoint=1)
            logging.info(f"After sending 'Off' command state is  {'ON' if on_off_stats else 'OFF'}")
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def start_iteration_logging(self, iteration_count, dut):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Create a file handler
        tc_log_path = os.path.join(self.test_config_dict["iter_logs_dir"], str(iteration_count))
        if not os.path.exists(tc_log_path):
            os.makedirs(tc_log_path)
        log_filename = os.path.join(tc_log_path, f"log_{timestamp}.log")
        self.iteration_file_handler = logging.FileHandler(log_filename)

        # Set the format for log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.iteration_file_handler.setFormatter(formatter)
        self.iteration_file_handler.setLevel(logging.DEBUG)
        # Add the file handler to the logger
        self.logger.addHandler(self.iteration_file_handler)
        if dut:
            dut.start_log()

    def stop_iteration_logging(self, iteration_count, dut):
        logging.info('{} iteration completed'.format(iteration_count))
        self.logger.removeHandler(self.iteration_file_handler)
        self.iteration_file_handler.close()

    async def device_info(self, node_id: int = None, dev_ctrl: ChipDeviceCtrl = None, endpoint: int = 0,
                          user_defined_info: dict = None, include_default_info: bool = True) -> dict:

        '''
        extra_info: this parameter is optional,is used when user wants more basic info of device input must be list of
        dictionaries having this sample input format
        [{"info_name":Clusters.ClusterObjects.ClusterAttributeDescriptor}]
        [{"vendor-name":Clusters.BasicInformation.Attributes.VendorName}]
        return a dict containing Basic device info user can add more device info
        this same information will be displayed in the UI
        ex {"product_name":"light Bulb"} -> UI it will be displayed in Caps as "PRODUCT_NAME"

        '''
        info_dict = {}
        if include_default_info and user_defined_info is None:  # used when user wants only default info given by this function
            default_info_attributes = {"product name": Clusters.BasicInformation.Attributes.ProductName,
                                       "vendor name": Clusters.BasicInformation.Attributes.VendorName,
                                       "vendor id": Clusters.BasicInformation.Attributes.VendorID,
                                       "hardware version": Clusters.BasicInformation.Attributes.HardwareVersionString,
                                       "software version": Clusters.BasicInformation.Attributes.SoftwareVersionString,
                                       "product id": Clusters.BasicInformation.Attributes.ProductID}
        elif include_default_info:  # used when user wants default info from this function and also their own info
            default_info_attributes = {"product name": Clusters.BasicInformation.Attributes.ProductName,
                                       "vendor name": Clusters.BasicInformation.Attributes.VendorName,
                                       "vendor id": Clusters.BasicInformation.Attributes.VendorID,
                                       "hardware version": Clusters.BasicInformation.Attributes.HardwareVersionString,
                                       "software version": Clusters.BasicInformation.Attributes.SoftwareVersionString,
                                       "product id": Clusters.BasicInformation.Attributes.ProductID}
            default_info_attributes.update(user_defined_info)
        else:  # used when user wants only their info
            default_info_attributes = user_defined_info

        if dev_ctrl is None:
            dev_ctrl = self.default_controller
        if node_id is None:
            node_id = self.dut_node_id
        for device_attr in default_info_attributes:
            try:
                response = await dev_ctrl.ReadAttribute(node_id, [endpoint, default_info_attributes[device_attr]])
                attr_ret = response[endpoint][Clusters.Objects.BasicInformation][default_info_attributes[device_attr]]
                info_dict.update({device_attr: attr_ret})
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                info_dict.update({device_attr: f"cannot fetch info because {e}"})
        return info_dict

    async def get_heap_usage(self, node_id: int = None, dev_ctrl: ChipDeviceCtrl = None, endpoint: int = 0, ):
        if dev_ctrl is None:
            dev_ctrl = self.default_controller
        if node_id is None:
            node_id = self.dut_node_id
        clusters = [Clusters.SoftwareDiagnostics.Attributes.CurrentHeapUsed,
                    ]
        data = []
        for cluster in clusters:
            try:
                response = await dev_ctrl.ReadAttribute(node_id, [endpoint, cluster])
                attr_ret = response[endpoint][Clusters.Objects.SoftwareDiagnostics][cluster]
                data.append(attr_ret/1000)
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                data.append(f"error when reading reason {e} ")
        return data


def log_path_add_args(path):
    args = sys.argv
    args.append("--logs-path")
    args.append(path)
    sys.argv = args


def run_set_folder_path(timestamp, log_path) -> str:
    run_set_folder = "RUN_SET_" + timestamp.strftime("%d_%b_%Y_%H-%M-%S")
    path = os.path.join(log_path, run_set_folder)
    if os.path.exists(path):
        return path
    else:
        os.mkdir(path)
        return path


def log_info_init(test_config_dict: dict):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tc_log_folder = os.path.join(test_config_dict["general_configs"]["logFilePath"], f"{timestamp}")
    test_config_dict.update({"iteration_id": timestamp})
    test_config_dict.update({"iter_logs_dir": tc_log_folder})
    test_config_dict.update({"current_iteration": 0})
    if not os.path.exists(tc_log_folder):
        os.makedirs(tc_log_folder)
    return test_config_dict


def add_args_commissioning_method(commissioning_method):
    copy_argv = sys.argv
    if "--commissioning-method" not in copy_argv:
        copy_argv.append("--commissioning-method")
        copy_argv.append(commissioning_method)
        sys.argv = copy_argv


def test_start(test_class_name):
    try:
        global dut_objects_list
        dict_args = convert_args_dict(sys.argv[1:])
        arg_keys = dict_args.keys()
        if "--yaml-file" in arg_keys:
            test_config_dict = yaml_config_reader(dict_args)
        else:
            test_config_dict = default_config_reader(dict_args)
        test_config_dict.update({"test_class_name": test_class_name})
        MatterQABaseTestCaseClass.test_config_dict = test_config_dict
        print(test_config_dict)
        general_configs = test_config_dict["general_configs"]
        log_path = general_configs["logFilePath"]
        if log_path is not None and os.path.exists(log_path):
            run_set_path = run_set_folder_path(datetime.datetime.now(), log_path)
            log_path = os.path.join(run_set_path, test_config_dict["test_class_name"])
            log_path_add_args(log_path)
            general_configs["logFilePath"] = log_path
        else:
            run_set_path = run_set_folder_path(datetime.datetime.now(), os.getcwd())
            log_path = os.path.join(run_set_path, test_config_dict["test_class_name"])
            log_path_add_args(path=log_path)
            general_configs["logFilePath"] = log_path
        if not os.path.exists(general_configs["logFilePath"]):
            os.mkdir(log_path)
        test_config_dict = log_info_init(test_config_dict)  # updating config dict with iter_log_dir and current_iter
        add_args_commissioning_method(general_configs["commissioning_method"])
        dut_object_loader(test_config_dict, dut_objects_list)
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
