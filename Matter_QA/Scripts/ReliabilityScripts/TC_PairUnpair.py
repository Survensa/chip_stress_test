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
import traceback
from Matter_QA.Configs import initializer
from Matter_QA.Library.BaseTestCases.MatterBaseQATestClass import reset, test_start, PairUnpairBaseClass
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, default_matter_test_main
from Matter_QA.Library.HelperLibs.utils import (CommissionTimeoutError, separate_logs_iteration_wise)


class TC_PairUnpair:

    @async_test_body
    async def test_tc_pair_unpair(self):
        try:
            _pass = 0
            _fail = 0
            platform = initializer.platform_execution
            iteration = int(initializer.iteration_number)
            self.pair_unpair_dut()
            logging.info('factory resetting the device for the next pairing')
            reset(platform, 1)
            for i in range(1, iteration + 1):
                logging.info('{} iteration of pairing sequence'.format(i))
                try:
                    iter_result = self.commission_device(kwargs={"timeout": initializer.dut_connection_timeout})
                except CommissionTimeoutError as e:
                    logging.error(e)
                    iter_result = False
                if iter_result:
                    logging.info('Device has been Commissioned starting pair-unpair operation')
                    time.sleep(2)
                    self.pair_unpair_dut()
                    logging.info(f'iteration {i} is passed and unpairing the device is successful')
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

                if i != iteration:
                    reset(platform, 1, iteration=i)
                    logging.info('Command to restart device is sent')

                else:
                    reset(platform, 0)
                    logging.info('This is the Last iteration which is completed, stopping the pair-unpair operation, '
                                 'resetting the DUT')
                time.sleep(2)
                logging.info('completed pair and unpair sequence for {}'.format(i))
            logging.info(f"The Summary of the {initializer.iteration_number} iteration are")
            logging.info(f"\t  \t  Pass:  {_pass}")
            logging.info(f"\t  \t  Fail:  {_fail}")
            separate_logs_iteration_wise()

        except Exception as e:
            logging.error(e)
            traceback.print_exc()


if __name__ == "__main__":
    PairUnpairBaseClass.test_tc_pair_unpair = TC_PairUnpair.test_tc_pair_unpair
    test_start()
    default_matter_test_main()
