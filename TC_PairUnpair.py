#
#    Copyright (c) 2022 Project CHIP Authors
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import datetime
import logging
import os
import threading
import time
import secrets
import sys
import traceback
from Matter_QA.Configs import initializer
from chip import ChipDeviceCtrl
from matter_testing_support import MatterBaseTest, async_test_body, default_matter_test_main
from Matter_QA.HelperLibs.utils import timer, CommissionTimeoutError, convert_args_dict, custom_dut_class_override, \
    separate_logs_iteration_wise
from Matter_QA.Platform.CustomDut import CustomDut
from Matter_QA.Platform.raspberryPiPlatform import Rpi


class TC_PairUnpair(MatterBaseTest):
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

    @async_test_body
    async def test_tc_pair_unpair(self):
        try:
            _pass = 0
            _fail = 0
            conf = self.matter_test_config
            platform = initializer.platform_execution
            iteration = int(initializer.iteration_number)
            self.th1 = self.default_controller
            time.sleep(3)
            self.th1.UnpairDevice(self.dut_node_id)
            time.sleep(3)
            self.th1.ExpireSessions(self.dut_node_id)
            time.sleep(3)
            logging.info('PLEASE FACTORY RESET THE DEVICE for the next pairing')
            reset(platform, 1)
            date = datetime.datetime.now().isoformat()[:-7].replace(":", "_")
            for i in range(1, iteration + 1):
                logging.info('{} iteration of pairing sequence'.format(i))
                try:
                    iter_result = self.commission_device(kwargs={"timeout": initializer.dut_connection_timeout})
                except CommissionTimeoutError as e:
                    logging.error(e)
                    iter_result = False
                if iter_result:
                    logging.info('unpairing the device')
                    time.sleep(2)
                    self.th1.UnpairDevice(self.dut_node_id)
                    self.th1.ExpireSessions(self.dut_node_id)
                    logging.info(f'iteration {i} is passed')
                    _pass += 1

                else:
                    logging.error(f'iteration {i} is failed')
                    _fail += 1
                    if not initializer.execution_mode_full:
                        logging.info(
                            'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                            'execution will stop here'.format(
                                i))
                        reset(platform, 1)
                        logging.info('thread completed')
                        break
                logging.info('PLEASE FACTORY RESET THE DEVICE')

                if i != iteration:
                    reset(platform, 1, iteration=i)
                    logging.info('thread completed')

                else:
                    reset(platform, 0)
                    logging.info('thread completed')
                time.sleep(2)
                logging.info('completed pair and unpair sequence for {}'.format(i))

            logging.info(f"The Summary of the {initializer.iteration_number} iteration are")
            logging.info(f"\t  \t  Pass:  {_pass}")
            logging.info(f"\t  \t  Fail:  {_fail}")
            separate_logs_iteration_wise()

        except Exception as e:
            logging.error(e)
            traceback.print_exc()


def test_start():
    log_file = "TC_PairUnpair_log.txt"
    dict_args = convert_args_dict(sys.argv[1:])
    initializer.read_yaml(dict_args["--yaml-file"])
    if initializer.platform_execution != 'rpi':
        custom_dut_class_override()
    copy_argv = sys.argv
    copy_argv.append("--commissioning-method")
    copy_argv.append(initializer.commissioning_method)
    sys.argv = copy_argv
    if os.path.exists(log_file):
        os.remove(log_file)
    if initializer.platform_execution == 'rpi':
        logging.info("advertising the dut")
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
        Rpi().factory_reset(i)
        time.sleep(2)

    elif platform == 'CustomDut':
        logging.info("CUSTOM DUT device is going to be reset")
        CustomDut().factory_reset(i, iteration)
    logging.info('Iteration has been completed')
    return True


if __name__ == "__main__":
    test_start()
    default_matter_test_main()
