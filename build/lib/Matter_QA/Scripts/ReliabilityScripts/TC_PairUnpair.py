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
from Matter_QA.Library.BaseTestCases import MatterQABaseTestClass
from Matter_QA.Library.BaseTestCases import MatterDUTNodeClass

from Matter_QA.Configs import initializer
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, default_matter_test_main
from Matter_QA.Library.HelperLibs.utils import (CommissionTimeoutError, convert_args_dict,
                                                custom_dut_class_override, separate_logs_iteration_wise)
from Matter_QA.Library.Platform.CustomDut import CustomDut
from Matter_QA.Library.Platform.raspi.raspberryPiPlatform import Rpi
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import PairUnpairBaseClass

class TC_PairUnpair(MatterQABaseTestClass, MatterDUTNodeClass):
    def __init__(self, *args):
        self._pass = 0
        self._fail = 0
        self.dut = MatterDUTNodeClass()

    @async_test_body
    async def test_tc_pair_unpair(self):
        try:
            # DUT node is paired in the MatterBaseTest class
            self.unpair_dut()
            logging.info('facotry resetting the device for the next pairing')
            self.dut.factory_reset()
            # TODO: FIX
            self.config.iteration = 1000
            for iteration_count in range(1, self.config.iteration + 1):
                logging.info('{} iteration of pairing sequence'.format(iteration_count))
                try:
                    iter_result = self.commission_device(kwargs={"timeout": initializer.dut_connection_timeout})
                except CommissionTimeoutError as e:
                    logging.error(e)
                    iter_result = False
                if iter_result:
                    logging.info(f'iteration {iteration_count} is passed and unpairing the device')
                    # TODO Fix
                    time.sleep(3)
                    self.unpair_dut()
                    self._pass += 1

                else:
                    logging.error(f'iteration {iteration_count} is failed')
                    self._fail += 1
                    if not self.continue_test_execution():
                        break
              
                self.dut.factory_reset()
    
            logging.info(f"The Summary of the {initializer.iteration_number} iteration are")
            logging.info(f"\t  \t  Pass:  {self._pass}")
            logging.info(f"\t  \t  Fail:  {self._fail}")
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

if __name__ == "__main__":
    test_start()
    default_matter_test_main()
