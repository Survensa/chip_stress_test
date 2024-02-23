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
import time

from serial import Serial
import logging
import traceback
from mobly import signals


class SerialPort(object):
    def __init__(self, port, baudrate, timeout) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port_obj = Serial(self.port, self.baudrate, timeout=self.timeout)

    def open_serial(self):
        try:
            if not self.serial_port_obj.is_open:
                logging.info("Opening Serial Port")
                self.serial_port_obj.open()
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def write_cmd(self, cmd):
        try:
            self.serial_port_obj.write(cmd)
            self.serial_port_obj.flush()
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
