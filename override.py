import serial
import time
import logging
import os
from invoke import UnexpectedExit
import sys
from mobly import signals


def reboot(self):
    # As of now the nRF52840-DK is not able to reboot
    return (self.factory_reset())


def factory_reset(self, i):
    Serial_port().write_cmd()
    time.sleep(2)
    if i == 0:
        self.stop_logging()

    return True


def advertise(self):
    # Since the advertisement is done during factory_reset it can be skipped
    logging.info("advertising the DUT")
    return (self.factory_reset)


def start_logging(self, log):
    ser = Serial_port().create_serial()

    if ser.is_open:

        log_file = "dutlog/rpi_log.txt"
        current_dir = os.getcwd()
        log_path = os.path.join(current_dir, log_file)
        if os.path.exists(log_path):
            os.remove(log_path)

        log = open(log_path, 'w')

        try:
            while True:

                line = ser.readline().decode('utf-8').strip()

                if line:
                    print(line)

                    log.write(line + '\n')
                    log.flush()

        except UnexpectedExit:

            ser.close()
            log_file.close()


    else:
        logging.info("Failed to read the log in thread")
        sys.exit()

    return True


def stop_logging(self):
    ser = Serial_port().create_serial()
    ser.close()

    return True


class Serial_port(object):
    def __init__(self) -> None:
        self.port = "/dev/ttyACM1"
        self.baudrate = 115200
        self.timeout = 5

    def create_serial(self):
        ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        if not ser.is_open:
            ser.open()

        return ser

    def write_cmd(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=3)
        except serial.SerialException:
            raise signals.TestAbortAll("Failed to Reset the device")

        cmd = b'matter device factoryreset\n'

        for i in range(1, 4):
            ser.write(cmd)
            time.sleep(2)

        ser.close()
