#
#
#  Copyright (c) 2023 Project CHIP Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import datetime
import importlib.util
import traceback
import time
import logging
import os
from threading import Event, Thread
import sys
from Matter_QA.Library.BaseTestCases.BaseDUTNodeClass import BaseDutNodeClass, BaseNodeDutConfiguration
from Matter_QA.Library.HelperLibs.commonSerialInterface import SerialPort

event_closer = Event()


class NordicDut(BaseDutNodeClass, BaseNodeDutConfiguration):
    def __init__(self, test_config) -> None:
        super().__init__(test_config)
        self.test_config = test_config

        self.serial_port = SerialPort(port=self.test_config.nordic_config.serial_port,
                                                          baudrate=self.test_config.nordic_config.serial_baudrate,
                                                          timeout=self.test_config.nordic_config.serial_timeout)
        self.serial_port.open_serial()

    def reboot_dut(self):
        pass

    def factory_reset_dut(self, stop_reset: bool):
        if not stop_reset:
            # self.stop_logging()
            for i in range(1, 4):
                logging.info("resetting nordic matter device")
                if self.serial_port.serial_port_obj.is_open:
                    self.serial_port.write_cmd(b'matter device factoryreset\n')
                    time.sleep(5)
                else:
                    logging.info("The port was closed now opening the port")
                    self.serial_port.serial_port_obj.open()
                    self.serial_port.write_cmd(b'matter device factoryreset\n')
            return True
        else:
            self.start_matter_app()
            logging.info("completed advertising of DUT")
            return True

    def start_matter_app(self):
        try:
            if self.serial_port.serial_port_obj.is_open:
                self.serial_port.write_cmd(b'matter device factoryreset\n')
                time.sleep(5)
            else:
                logging.info("The port was closed now opening the port")
                self.serial_port.serial_port_obj.open()
                self.serial_port.write_cmd(b'matter device factoryreset\n')
            return True
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def start_logging(self, log=None) -> bool:
        global event_closer
        if not self.serial_port.serial_port_obj.is_open:
            self.serial_port.open_serial()
        if self.test_config.current_iteration == 0:
            self.test_config.current_iteration += 1
        if self.serial_port.serial_port_obj.is_open:
            while self.serial_port.serial_port_obj.is_open:
                try:
                    current_dir = self.test_config.iter_logs_dir
                    log_path = os.path.join(current_dir, str(self.test_config.current_iteration))
                    if not os.path.exists(log_path):
                        os.mkdir(log_path)
                    log_file = os.path.join(log_path, "Dut_log_{}_"
                                            .format(str(self.test_config.current_iteration)) +
                                            str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                            + ".log"
                                            )
                    logging.info("started to read buffer")
                    data = self.serial_port.serial_port_obj.read_until(b'Done\r\r\n').decode()
                    logging.info("completed read from buffer")
                    if data == '':
                        logging.info("data not present in buffer breaking from read loop")
                        break
                    with open(log_file, 'w') as fp:
                        fp.write(data)
                        logging.info("completed write to file")

                except Exception as e:
                    print(e)
                    traceback.print_exc()
            self.serial_port.serial_port_obj.close()
        else:
            logging.info("Failed to read the log in thread")
            sys.exit()
        logging.info("closing the Log File")
        return True

    def stop_logging(self):
        global event_closer
        event_closer.set()
        return True

    def pre_iteration_loop(self):
        pass

    def post_iteration_loop(self):
        pass


def create_dut_object(test_config):
    dut_obj = NordicDut(test_config=test_config)
    thread = Thread(target=dut_obj.start_logging)
    thread.start()
    dut_obj.factory_reset_dut(stop_reset=False)
    return dut_obj
