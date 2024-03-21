import logging
import sys
from serial import Serial


log = logging.getLogger("serial")

class SerialConnection:
    def __init__(self, serial_config):
        self.port = serial_config.serial_port
        self.baudrate = serial_config.baudrate
        self.timeout = serial_config.timeout

        try:
            self.serial_object = Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            log.error(f"could not connect to Nordic DUT: {e}")
            sys.exit(1)

    def send_command(self, command, **kwargs):
        try:
            output = self.serial_object.write(command, **kwargs)
            self.serial_object.flush()
            return output
        except Exception as e:
            self.logger.error(str(e), exc_info=True)

    def open_serial_connection(self):
        self.serial_object.open()

    def close_serial_connection(self):
        self.serial_object.close()