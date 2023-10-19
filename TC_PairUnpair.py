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
import time
import secrets
import signal
import sys
from io import StringIO
import traceback
import config
import chip.CertificateAuthority
import chip.clusters as Clusters
import chip.clusters.enum
import chip.FabricAdmin
from chip import ChipDeviceCtrl
from chip.ChipDeviceCtrl import CommissioningParameters
from matter_testing_support import MatterBaseTest, async_test_body, default_matter_test_main, parse_matter_test_args
from mobly import asserts
from chip.utils import CommissioningBuildingBlocks
from chip.clusters import OperationalCredentials as opCreds
from mobly import asserts, base_test, signals, utils
from invoke.exceptions import UnexpectedExit
from reset import CustomDut, reset, test_start, test_stop


class CommissionTimeoutError(Exception):
    pass


def logger_function(iternation_number,date,log_file_path)->logging:
            logger = logging.getLogger("{}_{}.log".format(date,str(iternation_number)))
            logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler("{}/iteration_{}_{}.log".format(log_file_path,str(iternation_number),date))
            logger.addHandler(fh)
            formatter = logging.Formatter('%(levelname)s:%(message)s')
            fh.setFormatter(formatter)
            #logger.propagate = False
            return logger


iteration_logger:logging

def timeouterror(signum, frame):
    raise CommissionTimeoutError("timed out, Failed to commission the dut")


def timer(function):
    def wrapper(*args, **kwargs):
        # Set the alarm for the timeout
        timeout = kwargs.pop('timeout', 60)
        signal.signal(signal.SIGALRM, timeouterror)
        signal.alarm(timeout)

        try:
            result = function(*args, **kwargs)
        finally:
            # Cancel the alarm after the function finishes
            signal.alarm(0)

        return result

    return wrapper


args = sys.argv[1:]


# conf_gl=convert_args_dict(args)


class TC_PairUnpair(MatterBaseTest):
    # global conf_gl
    @timer
    def commission_device(self, *args, **kwargs):
        global iteration_logger
        conf = self.matter_test_config
        for commission_idx, node_id in enumerate(conf.dut_node_ids):
            iteration_logger.info("Starting commissioning for root index %d, fabric ID 0x%016X, node ID 0x%016X" %
                         (conf.root_of_trust_index, conf.fabric_id, node_id))
            iteration_logger.info("Commissioning method: %s" % conf.commissioning_method)

            if not self._commission_device(commission_idx,iteration_logger):
                return False

            else:
                return True

    def _commission_device(self, i, iteration_logger) -> bool:
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
                iteration_logger.warning("==== USING A DIRECT IP COMMISSIONING METHOD NOT SUPPORTED IN THE LONG TERM ====")
                return dev_ctrl.CommissionIP(
                    ipaddr=conf.commissionee_ip_address_just_for_testing,
                    setupPinCode=conf.setup_passcodes[i], nodeid=conf.dut_node_ids[i]
                )
            else:
                iteration_logger.error("Invalid commissioning method %s!" % conf.commissioning_method)
                raise ValueError("Invalid commissioning method %s!" % conf.commissioning_method)
        except Exception as e:
            iteration_logger.error(e)
            traceback.print_exc()
    @async_test_body
    async def test_TC_PairUnpair(self):
        _pass = 0
        _fail = 0
        conf = self.matter_test_config
        platform = config.platform_execution
        iteration = int(config.iteration_number)
        self.th1 = self.default_controller
        time.sleep(3)
        self.th1.UnpairDevice(self.dut_node_id)
        self.th1.ExpireSessions(self.dut_node_id)
        time.sleep(3)
        logging.info('PLEASE FACTORY RESET THE DEVICE for the next pairing')
        reset(platform, 1)
        date=datetime.datetime.now().isoformat()[:-7].replace(":","_")
        for i in range(1, iteration + 1):
            global iteration_logger
            iteration_logger=logger_function(date=date,iternation_number=str(i),log_file_path=config.log_file_path)
            iteration_logger.info('{} iteration of pairing sequence'.format(i))
            try:
                iter = self.commission_device(kwargs={"timeout": config.dut_connection_timeout})
            except CommissionTimeoutError as e:
                iteration_logger.error(e)
                iter = False
            if iter:
                iteration_logger.info('unpairing the device')
                time.sleep(2)
                self.th1.UnpairDevice(self.dut_node_id)
                self.th1.ExpireSessions(self.dut_node_id)
                iteration_logger.info(f'iteration {i} is passed')
                _pass += 1

            else:
                iteration_logger.error(f'iteration {i} is failed')
                _fail += 1
                if not config.execution_mode_full:
                    iteration_logger.info(
                        'Full Execution mode is disabled \n The iteration {} number has failed hence the execution will stop here'.format(
                            i))
                    reset(platform, 1)
                    iteration_logger.info('thread completed')
                    break
            iteration_logger.info('PLEASE FACTORY RESET THE DEVICE')

            if i != iteration:
                reset(platform, 1)
                iteration_logger.info('thread completed')

            else:
                reset(platform, 0)
                iteration_logger.info('thread completed')
            time.sleep(2)
            iteration_logger.info('completed pair and unpair sequence for {}'.format(i))

        logging.info(f"The Summary of the {config.iteration_number} iteration are")
        logging.info(f"\t  \t  Pass:  {_pass}")
        logging.info(f"\t  \t  Fail:  {_fail}")


if __name__ == "__main__":
    test_start()
    log_file = "TC_PairUnpair_rpi_log.txt"
    default_matter_test_main()