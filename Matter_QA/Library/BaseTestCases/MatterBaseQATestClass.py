import logging
import secrets
import sys
import threading
import time
import traceback
import os
from Matter_QA.Library.HelperLibs.matter_testing_support import MatterBaseTest,async_test_body
from Matter_QA.Configs import initializer
from Matter_QA.Library.HelperLibs.utils import (timer, CommissionTimeoutError,
                                                convert_args_dict,custom_dut_class_override)
from chip import ChipDeviceCtrl

from Matter_QA.Library.Platform.raspberryPiPlatform import Rpi
from Matter_QA.Library.Platform.CustomDut import CustomDut


class PairUnpairBaseClass(MatterBaseTest):
    def __init__(self, *args):
        super().__init__(*args)
        self.th1 = None

    @timer
    def commission_device(self, *args, **kwargs):
        conf = self.matter_test_config
        for commission_idx, node_id in enumerate(conf.dut_node_id):
            logging.info("Starting commissioning for root index %d, fabric ID 0x%016X, node ID 0x%016X" %
                         (conf.root_of_trust_index, conf.fabric_id, node_id))
            logging.info("Commissioning method: %s" % conf.commissioning_method)

            if not self._commission_device(commission_idx):
                return False

            else:
                return True

    def _commission_device(self, i) -> bool:
        try:
            dev_ctrl = self.default_controller
            conf = self.matter_test_config
            random_nodeid = secrets.randbelow(2 ** 32)
            conf.dut_node_id = [random_nodeid]
            DiscoveryFilterType = ChipDeviceCtrl.DiscoveryFilterType

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

    def pair_unpair_dut(self):
        try:
            self.th1 = self.default_controller
            time.sleep(3)
            self.th1.UnpairDevice(self.dut_node_id)
            time.sleep(3)
            self.th1.ExpireSessions(self.dut_node_id)
            time.sleep(3)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
    
    @async_test_body
    async def test_tc_pair_unpair(self):
        pass



def test_start():
    
    dict_args = convert_args_dict(sys.argv[1:])
    initializer.read_yaml(dict_args["--yaml-file"])
    if initializer.platform_execution != 'rpi':
        custom_dut_class_override()
    
    if initializer.platform_execution == 'rpi':
        log_file = initializer.dut_log_path+"/TC_PairUnpair_log.txt"
        if os.path.exists(log_file):
            os.remove(log_file)
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


def test_stop(platform):
    if platform == 'rpi':
        Rpi().stop_logging()

    elif platform == 'thread':
        CustomDut().stop_logging()


def reset(platform, i, iteration=0):
    if platform == "rpi":
        logging.info("RaspberryPI DUT device is going to be reset")
        Rpi().factory_reset(i)
        time.sleep(2)

    elif platform == 'CustomDut':
        logging.info("CUSTOM DUT device is going to be reset")
        CustomDut().factory_reset(i, iteration)
    logging.info('Iteration has been completed')
    return True