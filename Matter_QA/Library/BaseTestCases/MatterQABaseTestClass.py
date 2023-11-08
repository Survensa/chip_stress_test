import logging
import datetime
import secrets
import time
import traceback
import os
import threading
import sys
import argparse
import io
import yaml
import importlib.util
from Matter_QA.Library.HelperLibs.matter_testing_support import MatterBaseTest
from Matter_QA.Library.HelperLibs.utils import timer, convert_args_dict
from Matter_QA.Library.Platform.raspberrypi import raspi
from chip import ChipDeviceCtrl

dut_objects_list = []


class MatterQABaseTestCaseClass(MatterBaseTest):
    test_config_dict = {}

    def __init__(self, *args):
        super(MatterBaseTest, self).__init__(*args)
        self.logger = logging.getLogger('')
        self.logger.setLevel(logging.DEBUG)  # Set the logger's level
        self.test_config_dict = MatterQABaseTestCaseClass.test_config_dict
        self.dut = None
        self.__misc_int()

    def get_dut_object(self):
        global dut_objects_list
        if len(dut_objects_list) > 0:
            return dut_objects_list[0]
        else:
            logging.error("Dut object is not initialized")
            # sys.exit(0)
        # self.create_dut_object()

    def __misc_int(self):
        self.th1 = None
        self.test_result = {'Pass Count': 0, 'Fail Count': {'Count': 0, 'Iteration': []}, 'Error Count': 0}
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.tc_log_folder = os.path.join(self.matter_test_config.logs_path, f"{timestamp}")
        if not os.path.exists(self.tc_log_folder):
            os.makedirs(self.tc_log_folder)

    @timer
    def commission_device(self, *args, **kwargs):
        conf = self.matter_test_config
        for commission_idx, node_id in enumerate(conf.dut_node_id):
            try:
                logging.info("Starting commissioning for root index %d, fabric ID 0x%016X, node ID 0x%016X" %
                             (conf.root_of_trust_index, conf.fabric_id, node_id))
                logging.info("Commissioning method: %s" % conf.commissioning_method)
                if not self._commission_device(commission_idx):
                    return False
                else:
                    return True
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                return False

    def _commission_device(self, i) -> bool:
        try:
            dev_ctrl = self.default_controller
            conf = self.matter_test_config
            random_nodeid = secrets.randbelow(2 ** 32)
            conf.dut_node_id = [random_nodeid]
            DiscoveryFilterType = ChipDeviceCtrl.DiscoveryFilterType
            # TODO: support by manual code and QR

            if conf.commissioning_method == "on-network":
                return dev_ctrl.CommissionOnNetwork(
                    nodeId=conf.dut_node_id[i],
                    setupPinCode=conf.setup_passcode[i],
                    filterType=DiscoveryFilterType.LONG_DISCRIMINATOR,
                    filter=conf.discriminator[i]
                )
            elif conf.commissioning_method == "ble-wifi":
                return dev_ctrl.CommissionWiFi(
                    conf.discriminator[i],
                    conf.setup_passcode[i],
                    conf.dut_node_id[i],
                    conf.wifi_ssid,
                    conf.wifi_passphrase
                )
            elif conf.commissioning_method == "ble-thread":
                return dev_ctrl.CommissionThread(
                    conf.discriminator[i],
                    conf.setup_passcode[i],
                    conf.dut_node_id[i],
                    conf.thread_operational_dataset
                )
            elif conf.commissioning_method == "on-network-ip":
                logging.warning("==== USING A DIRECT IP COMMISSIONING METHOD NOT SUPPORTED IN THE LONG TERM ====")
                return dev_ctrl.CommissionIP(
                    ipaddr=conf.commissionee_ip_address_just_for_testing,
                    setupPinCode=conf.setup_passcode[i], nodeid=conf.dut_node_id[i]
                )
            else:
                logging.error("Invalid commissioning method %s!" % conf.commissioning_method)
                raise ValueError("Invalid commissioning method %s!" % conf.commissioning_method)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            return False

    def unpair_dut(self):
        self.th1 = self.default_controller
        self.th1.UnpairDevice(self.dut_node_id)
        time.sleep(3)
        self.th1.ExpireSessions(self.dut_node_id)
        time.sleep(3)

    def start_iteration_logging(self, iteration_count, dut):

        test_class = self.__class__.__name__
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Create a file handler
        tc_log_path = os.path.join(self.tc_log_folder, test_class, str(iteration_count))
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
        # self.log.addHandler(self.iteration_file_handler)
        # stream_handler = logging.StreamHandler()
        # stream_handler.setFormatter(formatter)
        # logger.addHandler(stream_handler)

        # self.iteration_log = logger

        if dut:
            dut.start_log()
        pass

    def stop_iteration_logging(self, iteration_count, dut):
        logging.info('{} iteration completed'.format(iteration_count))
        self.logger.removeHandler(self.iteration_file_handler)
        self.iteration_file_handler.close()
        """
        for h in self.iteration_log.handlers:
            self.iteration_log.removeHandler(h)
            if isinstance(h, logging.FileHandler):
                h.close()
        if dut:          
            dut.start_log()
        pass
        """

    def continue_test_execution(self):
        # TODO Fix
        """
        if not initializer.execution_mode_full:
                logging.info(
                            'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                            'execution will stop here'.format(
                                i))
            reset(platform, 1)
                logging.info('thread completed')
        """


def log_path_add_args(path):
    args = sys.argv
    args.append("--logs-path")
    args.append(path)


def add_args_commissioning_method(commissioning_method):
    copy_argv = sys.argv
    if "--commissioning-method" not in copy_argv:
        copy_argv.append("--commissioning-method")
        copy_argv.append(commissioning_method)
        sys.argv = copy_argv


def test_start():
    # parser = argparse.ArgumentParser(description="parser to parse testcase args")
    # parser.add_argument('--configYaml', help="Input Configuration YAML file ")
    # args = parser.parse_args()
    # config_yaml_file = args.configYaml
    try:
        global dut_objects_list
        dict_args = convert_args_dict(sys.argv[1:])
        if not os.path.exists(dict_args["--yaml-file"]):
            logging.error("The config file does not exist! exiting now! ")
            sys.exit(0)
        config_yaml_file = dict_args["--yaml-file"]
        with io.open(config_yaml_file, 'r') as f:
            test_config_dict = yaml.safe_load(f)
        MatterQABaseTestCaseClass.test_config_dict = test_config_dict
        print(test_config_dict)
        general_configs = test_config_dict["general_configs"]
        log_path = general_configs["logFilePath"]
        if log_path is not None and os.path.exists(log_path):
            log_path_add_args(log_path)
        else:
            log_path_add_args(path=os.getcwd())
            general_configs["logFilePath"] = os.getcwd()
        add_args_commissioning_method(general_configs["commissioning_method"])
        if general_configs['platform_execution'] != 'rpi' and \
                'deviceModules' in general_configs.keys():
            module_path = general_configs['deviceModules']['module_path']
            module_name = general_configs['deviceModules']['module_name']
            if not os.path.exists(os.path.join(module_path, module_name)):
                logging.error('Error in importing Module! check if file exists')
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            dut_objects_list.append(module.create_dut_obect(test_config_dict))
        elif general_configs['platform_execution'] == 'rpi':
            logging.info("RaspberryPi Platform is selected")
            dut_objects_list.append(raspi.create_dut_object(test_config=test_config_dict))
            logging.info("Starting Matter DUT application")
            raspi.Raspi(test_config=test_config_dict).factory_reset_dut(stop_reset=False)
    except Exception as e:
        logging.error(e)
        traceback.print_exc()


def register_dut_module():
    dut_objects_list.append()


"""
def test_start():
    log_file = "TC_PairUnpair_log.txt"
    dict_args = convert_args_dict(sys.argv[1:])

    with io.open(utils.abs_path(path), 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(dict_args["--yaml-file"])
    return conf
    initializer.read_yaml(dict_args["--yaml-file"])
    if initializer.platform_execution != 'rpi':
        custom_dut_class_override()

    if os.path.exists(log_file):
        os.remove(log_file)
    if initializer.platform_execution == 'rpi':
        print("advertising the dut")
        thread = threading.Thread(target=Rpi().advertise)
        thread.start()
        time.sleep(5)

    elif initializer.platform_execution == 'CustomDut':
        thread = threading.Thread(target=CustomDut().start_logging)
        thread.start()
        CustomDut().advertise(iteration=0)
        time.sleep(5)

    return True


    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Find the test class in the test script.
        test_class = self.__class__.__name__
        log_filename = os.path.join(self.matter_test_config.logs_path,test_class,str(iteration_count),f"log_{timestamp}.log")
        
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            filename=log_filename,
                            filemode='w'  # Use 'a' if you want to append to an existing log file
                            )
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        default_logger = logging.getLogger('matter_qa_base_test_class')
        default_logger.addHandler(handler)
        default_logger.setLevel(logging.DEBUG)
        default_logger.info('{} iteration of pairing sequence'.format(iteration_count))
        self.iteration_log = default_logger     
"""
