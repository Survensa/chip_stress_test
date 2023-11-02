import logging
import secrets
import time
import traceback
import os
import threading
import sys
import traceback
from Matter_QA.Library.HelperLibs.matter_testing_support import MatterBaseTest
from Matter_QA.Library.HelperLibs.utils import (timer, CommissionTimeoutError)
from chip import ChipDeviceCtrl


class MatterQABaseTestClass(MatterBaseTest):
    def __init__(self, *args):
        super().__init__(*args)
        self.th1 = None

    @timer
    def commission_device(self, *args, **kwargs):
        conf = self.matter_test_config
        for commission_idx, node_id in enumerate(conf.dut_node_ids):
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
            conf.dut_node_ids = [random_nodeid]
            DiscoveryFilterType = ChipDeviceCtrl.DiscoveryFilterType
            # TODO: support by manual code and QR

            if conf.commissioning_method == "on-network":
                return dev_ctrl.CommissionOnNetwork(
                    nodeId=conf.dut_node_ids[i],
                    setupPinCode=conf.setup_passcodes[i],
                    filterType=DiscoveryFilterType.LONG_DISCRIMINATOR,
                    filter=conf.discriminators[i]
                )
            elif conf.commissioning_method == "ble-wifi":
                return dev_ctrl.CommissionWiFi(
                    conf.discriminators[i],
                    conf.setup_passcodes[i],
                    conf.dut_node_ids[i],
                    conf.wifi_ssid,
                    conf.wifi_passphrase
                )
            elif conf.commissioning_method == "ble-thread":
                return dev_ctrl.CommissionThread(
                    conf.discriminators[i],
                    conf.setup_passcodes[i],
                    conf.dut_node_ids[i],
                    conf.thread_operational_dataset
                )
            elif conf.commissioning_method == "on-network-ip":
                logging.warning("==== USING A DIRECT IP COMMISSIONING METHOD NOT SUPPORTED IN THE LONG TERM ====")
                return dev_ctrl.CommissionIP(
                    ipaddr=conf.commissionee_ip_address_just_for_testing,
                    setupPinCode=conf.setup_passcodes[i], nodeid=conf.dut_node_ids[i]
                )
            else:
                logging.error("Invalid commissioning method %s!" % conf.commissioning_method)
                raise ValueError("Invalid commissioning method %s!" % conf.commissioning_method)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def unpair_dut(self):
        self.th1 = self.default_controller
        self.th1.UnpairDevice(self.dut_node_id)
        time.sleep(3)
        self.th1.ExpireSessions(self.dut_node_id)
        time.sleep(3)
    
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
class MatterDUTNodeClass:
    def __init__(self) -> None:
        pass

    def factory_reset():
        pass

def test_start():
    log_file = "TC_PairUnpair_log.txt"
    dict_args = convert_args_dict(sys.argv[1:])
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