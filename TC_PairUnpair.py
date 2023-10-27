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
import re
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
from reset import CustomDut, reset, test_start, test_stop,convert_args_dict


class CommissionTimeoutError(Exception):
    pass

def timeouterror(signum, frame):
    raise CommissionTimeoutError("timed out, Failed to commission the dut")

def log_file_finder():
    dict_args=convert_args_dict(sys.argv[1:])
    log_file_path=dict_args["--logs-path"]
    dirs=os.listdir(log_file_path+"/MatterTest")
    logging.info("files present in {}".format(dirs))
    file_info_dict={}
    for i in dirs:
        file_info_dict[os.stat(log_file_path+"/MatterTest/"+i).st_mtime]=i
    keys=sorted(list(file_info_dict.keys()))
    latest_log_file_dir=log_file_path+"/MatterTest/"+file_info_dict[keys[-1]]
    logging.info("Folder containg latest logs {}".format(latest_log_file_dir))
    return {"latest_log_file_dir":latest_log_file_dir,"log_file_path":log_file_path}
def seprate_logs_iteration_wise():
    log_paths_dict=log_file_finder()
    log_file_directory=log_paths_dict["latest_log_file_dir"]
    fp=open(log_file_directory+"/test_log.INFO")
    data=fp.read()
    fp.close()
    result=re.findall(r"(\d+-\d+ \d+:\d+:\d+\.\d+ INFO (\d+) iteration of pairing sequence(.*?)\d+-\d+ \d+:\d+:\d+\.\d+ INFO completed pair and unpair sequence for \d+)",data,re.DOTALL)
    i=0
    for res in result:
        i+=1
        fp=open(config.log_file_path_iterations+"/iteration_logs_"+str(int(i))+"_"+datetime.datetime.now().isoformat().replace(":","_").replace(".","_"),'w')
        fp.write(res[0])
        fp.close

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
    async def test_TC_PairUnpair(self):
        try:
            _pass = 0
            _fail = 0
            conf = self.matter_test_config
            platform = config.platform_execution
            iteration = int(config.iteration_number)
            self.th1 = self.default_controller
            time.sleep(3)
            self.th1.UnpairDevice(self.dut_node_id)
            time.sleep(3)
            self.th1.ExpireSessions(self.dut_node_id)
            time.sleep(3)
            logging.info('PLEASE FACTORY RESET THE DEVICE for the next pairing')
            reset(platform, 1)
            date=datetime.datetime.now().isoformat()[:-7].replace(":","_")
            for i in range(1, iteration + 1):
                logging.info('{} iteration of pairing sequence'.format(i))
                try:
                    iter = self.commission_device(kwargs={"timeout": config.dut_connection_timeout})
                except CommissionTimeoutError as e:
                    logging.error(e)
                    iter = False
                if iter:
                    logging.info('unpairing the device')
                    time.sleep(2)
                    self.th1.UnpairDevice(self.dut_node_id)
                    self.th1.ExpireSessions(self.dut_node_id)
                    logging.info(f'iteration {i} is passed')
                    _pass += 1

                else:
                    logging.error(f'iteration {i} is failed')
                    _fail += 1
                    if not config.execution_mode_full:
                        logging.info(
                            'Full Execution mode is disabled \n The iteration {} number has failed hence the execution will stop here'.format(
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

            logging.info(f"The Summary of the {config.iteration_number} iteration are")
            logging.info(f"\t  \t  Pass:  {_pass}")
            logging.info(f"\t  \t  Fail:  {_fail}")
            seprate_logs_iteration_wise()
            
        except Exception as e:
            logging.error(e)
            traceback.print_exc()


if __name__ == "__main__":
    test_start()
    log_file = "TC_PairUnpair_rpi_log.txt"
    default_matter_test_main()