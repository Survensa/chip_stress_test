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
