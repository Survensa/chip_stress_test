import serial
import logging
import traceback

class SerialPort(object):
    def __init__(self, port, baudrate, timeout) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port_obj = None

    def create_serial(self):
        try:
            serial_port_obj = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            if not serial_port_obj.is_open:
                logging.info("Opening Serial Port")
                serial_port_obj.open()
                self.serial_port_obj = serial_port_obj
            return serial_port_obj
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def write_cmd(self,cmd):
        try:
            self.serial_port_obj.write(cmd)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()



