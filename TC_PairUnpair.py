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

import logging
import time
import secrets

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
from invoke import UnexpectedExit
from reset import Nordic, reset, test_start


class TC_PairUnpair(MatterBaseTest):
   
    def commission_device(self):

        conf = self.matter_test_config
        
        for commission_idx, node_id in enumerate(conf.dut_node_ids):
            logging.info("Starting commissioning for root index %d, fabric ID 0x%016X, node ID 0x%016X" %
                         (conf.root_of_trust_index, conf.fabric_id, node_id))
            logging.info("Commissioning method: %s" % conf.commissioning_method)

            if not self._commission_device(commission_idx):
                raise signals.TestAbortAll("Failed to commission node")

    def _commission_device(self, i) -> bool:
        dev_ctrl = self.default_controller
        conf = self.matter_test_config
        random_nodeid =  secrets.randbelow(2**32)  
        conf.dut_node_ids = [random_nodeid ]
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
            raise ValueError("Invalid commissioning method %s!" % conf.commissioning_method)



    @async_test_body
    async def test_TC_PairUnpair(self):

        
        conf = self.matter_test_config

   
        number_of_iterations = conf.number_of_iterations 
        platform = conf.platform

        self.th1 = self.default_controller
        time.sleep(3)
        self.th1.UnpairDevice(self.dut_node_id)
        self.th1.ExpireSessions(self.dut_node_id)

        time.sleep(3)
        logging.info('PLEASE FACTORY RESET THE DEVICE for the next pairing')
        reset(platform,1)

                    
        for i in range(1, number_of_iterations):
            logging.info('{} iteration of pairing sequence'.format(i+1))
            self.commission_device()
            logging.info('unpairing the device')
            time.sleep(2)
            self.th1.UnpairDevice(self.dut_node_id)
            self.th1.ExpireSessions(self.dut_node_id)
            logging.info('PLEASE FACTORY RESET THE DEVICE')
                           
            if i+1 is not number_of_iterations:
                   reset(platform, 1)
                   logging.info('thread completed')

            else:
                   reset(platform, 0)
                   logging.info('thread completed')
            
            time.sleep(2)
            logging.info('completed pair and unpair sequence for {}'.format(i+1))


if __name__ == "__main__":
    
    conf = parse_matter_test_args(None)
    platform = conf.platform
    test_start(platform)
    
    default_matter_test_main()
