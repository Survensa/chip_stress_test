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
import secrets
import sys
import time
import traceback
import chip.clusters as Clusters
import chip.exceptions
from chip import ChipDeviceCtrl

from Matter_QA.Library.HelperLibs.matter_testing_support import MatterBaseTest
from Matter_QA.Library.HelperLibs.utils import (timer, convert_args_dict, dut_object_loader, yaml_config_reader,
                                                default_config_reader, summary_log)
from Matter_QA.Library.HelperLibs.analticalDataCapture import AnalyticalDataCapture

dut_objects_list = []


class MatterQABaseTestCaseClass(MatterBaseTest):

    def __init__(self, *args):
        """
        self.switch_case member is used a switch case statement for pulling analytics parameter,user must declare here as-well as in config file for self.switch_case to work.
        for pulling different analytics parameter user must write their own custom function
        """
        super().__init__(*args)
        self.logger = logging.getLogger('')
        self.logger.setLevel(logging.DEBUG)  # Set the logger's level
        self.test_config = MatterQABaseTestCaseClass.test_config
        self.dut = None
        self.pairing_duration_start = datetime.datetime.now()
        self.iterations_failure_reason = None
        self.full_execution_mode = self.test_config.general_configs.execution_mode_full
        self.current_iteration = None
        self.__misc__init()

        # creating an object to capture analytics data to json file
        self.analytics_capture_object = AnalyticalDataCapture(analytics_json=self.analytics_json,
                                                              test_config=self.test_config)
        self.iterations = self.test_config.general_configs.iteration_number
        self.analytics_functions_dict = {
            "pairing_duration_info": self.collect_pairing_info,
            "heap_usage": self.collect_dut_heap_usage
        }

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

    # initialize all counters before the iteration loop starts
    async def pre_iteration_loop(self):
        device_info = await self.device_info()  # pulls basic cluster information this is must be present at all times
        self.test_result.update({"device_basic_information": device_info})
        self.test_result.update({"Failed_iteration_details": {}})
        self.dut.pre_iteration_loop()

    async def start_iteration(self, iteration, **kwargs):
        """
        In this function we will set the iteration logger for separating the logs by iteration wise,
        we will also capture the starting time for pairing duration info here if user will set it in config file
        """
        self.current_iteration = iteration
        self.start_iteration_logging(self.current_iteration, None)
        logging.info("Started Iteration sequence {}".format(self.current_iteration))
        self.test_config.current_iteration = self.current_iteration
        await self.collect_all_basic_analytics_info(
            pairing_duration_info={"initialise": True})  # start to capture pairing duration info and other things

    def start_iteration_logging(self, iteration_count, dut):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Create a file handler
        tc_log_path = os.path.join(self.test_config.iter_logs_dir, str(iteration_count))
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
    # TODO harshith use matterBase Test class
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
                    return {"status": "success"}
                else:
                    logging.info(f'commission response {str(commission_response[0])}')
                    if len(commission_response) > 1:
                        return {"status": "failed", "failed_reason": str(commission_response[1])}
                    else:
                        return {"status": "failed", "failed_reason": str(commission_response[0])}
            except Exception as e:
                logging.error(e, exc_info=True)
                traceback.print_exc()
                return {"status": "failed", "failed_reason": str(e)}

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

    def unpair_dut(self, controller=None, node_id=None) -> dict:
        try:
            if controller is None and node_id is None:
                self.th1 = self.default_controller
                self.th1.UnpairDevice(self.dut_node_id)
                time.sleep(3)
                self.th1.ExpireSessions(self.dut_node_id)
                time.sleep(3)
                return {"status": "success"}
            else:
                controller.UnpairDevice(node_id)
                time.sleep(3)
                controller.ExpireSessions(node_id)
                time.sleep(3)
                return {"status": "success"}
        except Exception as e:
            logging.error(e, exc_info=True)
            if isinstance(e, chip.exceptions.ChipStackError):
                return {"status": "failed", "failed_reason": e.msg}
            else:
                return {"status": "failed", "failed_reason": str(e)}

    def stop_iteration_logging(self):
        logging.info('{} iteration completed'.format(self.current_iteration))
        self.logger.removeHandler(self.iteration_file_handler)
        self.iteration_file_handler.close()

    def check_execution_mode(self):
        if self.full_execution_mode:
            return "full_execution_mode"
        else:
            logging.info(
                'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                'execution will stop here'.format(self.current_iteration))
            return "partial_execution_mode"

    def end_of_iteration(self, iteration_result, failure_reason=None, **kwargs):
        try:
            if iteration_result == "failed":
                self.log_iteration_test_results(iteration_result=iteration_result,
                                                failure_reason=failure_reason)
            else:
                self.log_iteration_test_results(iteration_result=iteration_result)
            summary_log(test_result=self.test_result, test_config=self.test_config,
                        completed=False, analytics_json=self.analytics_json)
            self.stop_iteration_logging()
        except Exception as e:
            logging.error(str(e),exc_info=True)

    def end_of_test(self, **kwargs):
        try:
            summary_log(test_result=self.test_result, test_config=self.test_config,
                        completed=True, analytics_json=self.analytics_json)
            self.dut.post_iteration_loop()
        except Exception as e:
            logging.error(str(e),exc_info=True)

    def log_iteration_test_results(self, iteration_result: str, failure_reason=None):
        try:
            if iteration_result == "success":
                self.test_result["Pass Count"] += 1
            elif iteration_result == "failed":
                self.test_result["Failed_iteration_details"].update({str(self.current_iteration): failure_reason})
                self.test_result["Fail Count"]["Iteration"].append(self.current_iteration)
                self.test_result["Fail Count"]["Count"] += 1
                logging.error(f'Iteration Number {self.current_iteration} is failed due to reason {failure_reason}')
        except Exception as e:
            logging.error(str(e), exc_info=True)

    async def collect_all_basic_analytics_info(self, **kwargs):
        for analytics in kwargs.keys():
            await self.analytics_functions_dict.get(analytics)(**kwargs[analytics])

    async def collect_pairing_info(self, **kwargs):
        if "pairing_duration_info" in self.test_config.general_configs.analytics_parameters:
            if kwargs.get("initialise"):
                self.pairing_duration_start = datetime.datetime.now()
            else:
                pairing_duration = round((datetime.datetime.now() - self.pairing_duration_start).total_seconds(), 4)

                self.analytics_capture_object.capture_analytics_to_json(analytics_name="pairing_duration_info",
                                                                        analytics_data=pairing_duration,
                                                                        iteration_number=str(kwargs["iteration_number"])
                                                                        )

    async def collect_dut_heap_usage(self, **kwargs):
        if "heap_usage" in self.test_config.general_configs.analytics_parameters:
            heap_usage = await self.get_heap_usage(kwargs["node_id"], kwargs["dev_ctrl"], kwargs["endpoint"])
            self.analytics_capture_object.capture_analytics_to_json(analytics_name="heap_usage",
                                                                    analytics_data=heap_usage,
                                                                    iteration_number=str(kwargs["iteration_number"])
                                                                    )

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
            logging.error(e, exc_info=True)
            traceback.print_exc()

    async def device_info(self, node_id: int = None, dev_ctrl: ChipDeviceCtrl = None, endpoint: int = 0,
                          user_defined_info: dict = None, include_default_info: bool = True) -> dict:

        """
        extra_info: this parameter is optional,is used when user wants more basic info of device input must be list of
        dictionaries having this sample input format
        [{"info_name":Clusters.ClusterObjects.ClusterAttributeDescriptor}]
        [{"vendor-name":Clusters.BasicInformation.Attributes.VendorName}]
        return a dict containing Basic device info user can add more device info
        this same information will be displayed in the UI
        ex {"product_name":"light Bulb"} -> UI it will be displayed in Caps as "PRODUCT_NAME"

        """
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
                logging.error(e, exc_info=True)
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
                data = (attr_ret / 1000)
            except Exception as e:
                logging.error(f"Exception occurred when reading HEAP USAGE reason {e} ", exc_info=True)
                traceback.print_exc()
                data = -1
        return data

def test_start(test_class_name):
    try:
        global dut_objects_list
        dict_args = convert_args_dict(sys.argv[1:])
        arg_keys = dict_args.keys()
        if "--yaml-file" in arg_keys:
            test_config = yaml_config_reader(dict_args)
        else:
            test_config = default_config_reader()
        test_config.test_class_name = test_class_name
        MatterQABaseTestCaseClass.test_config = test_config  # initialise the base class with configs
        log_path = test_config.general_configs.logFilePath
        if log_path is not None and os.path.exists(log_path):
            run_set_path = run_set_folder_path(datetime.datetime.now(), log_path)
            log_path = os.path.join(run_set_path, test_config.test_class_name)
            log_path_add_args(log_path)  # this function will set log storage path for mobly
            test_config.general_configs.logFilePath = log_path
        else:
            run_set_path = run_set_folder_path(datetime.datetime.now(), os.getcwd())
            log_path = os.path.join(run_set_path, test_config.test_class_name)
            log_path_add_args(path=log_path)
            test_config.general_configs.logFilePath = log_path

        log_info_init(test_config)  # updating config dict with iter_log_dir and current_iter

        # Function will set the commissioning method for matter_support testing file
        add_args_commissioning_method(test_config.general_configs.commissioning_method)
        dut_object_loader(test_config, dut_objects_list)
    except Exception as e:
        logging.error(e, exc_info=True)
        traceback.print_exc()

def log_path_add_args(path):  # add log path to python args for matter_base_test class to store logs(used by mobly)
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


def log_info_init(test_config):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tc_log_folder = os.path.join(test_config.general_configs.logFilePath, f"{timestamp}")
    test_config.iteration_id = timestamp
    test_config.iter_logs_dir = tc_log_folder
    test_config.current_iteration = 0
    if not os.path.exists(tc_log_folder):
        os.makedirs(tc_log_folder)


def add_args_commissioning_method(commissioning_method):
    copy_argv = sys.argv
    if "--commissioning-method" not in copy_argv:
        copy_argv.append("--commissioning-method")
        copy_argv.append(commissioning_method)
        sys.argv = copy_argv
