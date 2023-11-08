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
import os
import sys
import time

from Matter_QA.Library.HelperLibs.utils import CommissionTimeoutError
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import MatterQABaseTestCaseClass, test_start
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, default_matter_test_main


class TC_Pair_1(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        print("Inside TC_Pair_1 init func")

    @async_test_body
    async def test_tc_pair_unpair(self):
        self.dut = self.get_dut_object()
        logging.info("Entering the test function")
        failed_iterations = []
        _pass = 0
        _fail = 0
        iterations = int(self.test_config_dict["general_configs"]["iteration_number"])
        self.dut.factory_reset_dut(stop_reset=False)
        for i in range(1, iterations+1):
            self.start_iteration_logging(i, None)
            try:
                iter_result = self.commission_device(kwargs={"timeout": self.test_config_dict["general_configs"]["dut_connection_timeout"]})
            except CommissionTimeoutError as e:
                logging.error(e)
                iter_result = False
            if iter_result:
                logging.info('Device has been Commissioned starting pair-unpair operation')
                time.sleep(2)
                self.unpair_dut()
                logging.info(f'iteration {i} is passed and unpairing the device is successful')
                _pass += 1
            else:
                failed_iterations.append(i)
                logging.error(f'iteration {i} is failed')
                _fail += 1
                if not self.test_config_dict["general_configs"]["execution_mode_full"]:
                    logging.info(
                        'Full Execution mode is disabled \n The iteration {} number has failed hence the '
                        'execution will stop here'.format(i))
                    self.dut.factory_reset_dut(stop_reset=True)
                    break
            logging.info("Started Iteration sequence {}".format(i))
            if i == iterations:
                self.dut.factory_reset_dut(stop_reset=True)
            else:
                self.dut.factory_reset_dut(stop_reset=False)
            self.stop_iteration_logging(i, None)
            logging.info('completed pair and unpair sequence for {}'.format(i))
        logging.info(f"The Summary of the {iterations} iterations are")
        logging.info(f"\t  \t  Pass:  {_pass}")
        logging.info("\t  \t  Fail:  {} and Iterations which failed are {}".format(_fail, failed_iterations))


if __name__ == "__main__":
    test_start()
    default_matter_test_main(testclass=TC_Pair_1)

"""
    @async_test_body
    async def test_TC_PairUnpair(self):
        self.th1 = self.default_controller
        time.sleep(5)
        self.th1.UnpairDevice(self.dut_node_id)
        self.th1.ExpireSessions(self.dut_node_id)
        time.sleep(5)
        logging.info('PLEASE FACTORY RESET THE DEVICE')
        argv = sys.argv[1:]

        parser.add_argument('-iter', '--number-of-iterations', required=False,
                            default=10, metavar=('number-of-iterations'), type=int)
        number_of_iterations = parser.parse_args(argv).number_of_iterations
        for i in range(1, number_of_iterations):
            logging.info('{} iteration of pairing sequence'.format(i))
            self.commission_device()
            logging.info('PLEASE FACTORY RESET THE DEVICE')
            logging.info('unpairing the device')
            time.sleep(10)
            self.th1.UnpairDevice(self.dut_node_id)
            self.th1.ExpireSessions(self.dut_node_id)
            time.sleep(5)
            logging.info('completed pair and unpair sequence')

"""
