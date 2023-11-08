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
from Matter_QA.Library.BaseTestCases.BaseDUTNodeClass import create_dut_object
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import test_start

from Matter_QA.Configs import initializer
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, default_matter_test_main
from Matter_QA.Library.HelperLibs.utils import (CommissionTimeoutError, convert_args_dict,
                                                custom_dut_class_override, separate_logs_iteration_wise)
from Matter_QA.Library.Platform.CustomDut import CustomDut
from Matter_QA.Library.Platform.raspberrypi.raspi import Rpi
from Matter_QA.Library.BaseTestCases.MatterQABaseTestClass import PairUnpairBaseClass


class TC_PairUnpair(MatterQABaseTestClass):
    def __init__(self, *args):
        self.dut = create_dut_object()

    @async_test_body
    async def test_tc_pair_unpair(self):
        try:
            # DUT node is paired in the MatterBaseTest class
            self.unpair_dut()
            logging.info('facotry resetting the device for the next pairing')
            self.dut.factory_reset()
            # TODO: FIX
            self.config.iteration = 1000
            for iteration_count in range(1, self.config.iteration):
                self.start_iteration_logging(iteration_count, self.dut)
                try:
                    iter_result = self.commission_device(kwargs={"timeout": initializer.dut_connection_timeout})
                    logging.info(f'iteration {iteration_count} is passed and now unpairing the device')
                    time.sleep(3)
                    self.unpair_dut()
                    self.test_result["Pass Count"] = self.test_result["Pass Count"] + 1
                except CommissionTimeoutError as e:
                    logging.error(f'iteration {iteration_count} is failed')
                    logging.error(e)
                    self.test_result["Fail Count"] = self.test_result["Fail Count"] + 1
                    self.test_result["Fail Count"]["Iteration"].append(iteration_count)
                    if not self.continue_test_execution():
                        break
                self.stop_iteration_logging(iteration_count, self.dut)
                self.dut.factory_reset()

            logging.info(f"The Summary of the {initializer.iteration_number} iteration are")
            logging.info(f"\t  \t  Pass:  {self._pass}")
            logging.info(f"\t  \t  Fail:  {self._fail}")
            separate_logs_iteration_wise()

        except Exception as e:
            logging.error(e)
            traceback.print_exc()


if __name__ == "__main__":
    test_start()
    default_matter_test_main()
