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
import threading
import time
import sys
import traceback
from Matter_QA.Configs import initializer
from Matter_QA.Library.HelperLibs.matter_testing_support import async_test_body, default_matter_test_main
from Matter_QA.Library.HelperLibs.utils import (CommissionTimeoutError, convert_args_dict,
                                                custom_dut_class_override, separate_logs_iteration_wise)
from Matter_QA.Library.Platform.CustomDut import CustomDut
from Matter_QA.Library.Platform.raspberryPiPlatform import Rpi
from Matter_QA.Library.BaseTestCases.PairUnpairBaseClass import PairUnpairBaseClass


class TC_PairUnpair():
    @async_test_body
    async def test_tc_pair_unpair(self):
        try:
            pairing_obj = PairUnpairBaseClass()
            _pass = 0
            _fail = 0
            platform = initializer.platform_execution
            iteration = int(initializer.iteration_number)
            pairing_obj.pair_unpair_dut()
            logging.info('PLEASE FACTORY RESET THE DEVICE for the next pairing')
            reset(platform, 1)
            for i in range(1, iteration + 1):
                logging.info('{} iteration of pairing sequence'.format(i))
                try:
                    iter_result = pairing_obj.commission_device(kwargs={"timeout": initializer.dut_connection_timeout})
                except CommissionTimeoutError as e:
                    logging.error(e)
                    iter_result = False
                if iter_result:
                    logging.info('unpairing the device')
                    time.sleep(2)
                    pairing_obj.pair_unpair_dut()
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
