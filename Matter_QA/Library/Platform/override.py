import datetime
import traceback
import serial
import time
import logging
import os
from threading import Event
import sys
from mobly import signals

event_closer = Event()


def reboot(self):
    # As of now the nRF52840-DK is not able to reboot
    return self.factory_reset()


def factory_reset(self, i, iteration):
    if i == 0:
        # self.stop_logging()
        SerialPort().write_cmd()
        return True
    else:
        self.advertise(iteration=iteration)
        logging.info("copleted advertising of DUT")
        return True


def advertise(self, iteration):
    # Since the advertisement is done during factory_reset it can be skipped
    # thread = threading.Thread(target=self.start_logging,args=('iteration_'+str(iteration)+'_log',))
    # thread.start()
    # thread.join()
    SerialPort().write_cmd()
    time.sleep(2)
    return True


def start_logging(self):
    global event_closer
    ser = SerialPort().create_serial()
    log_store_path = "CustomDeviceLogs/"
    current_dir = os.getcwd()
    log_path = os.path.join(current_dir, log_store_path)
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    if ser.is_open:
        while ser.is_open:
            try:
                logging.info("started to read buffer")
                data = ser.read_until(b'Done\r\r\n').decode()
                logging.info("completed read from buffer")
                # print(data)
                if data == '':
                    logging.info("data not present in buffer breaking from read loop")
                    break
                with open(log_path + str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_"),
                          'w') as fp:
                    fp.write(data)
                    logging.info("completed write to file")

            except Exception as e:
                print(e)
                traceback.print_exc()
    else:
        logging.info("Failed to read the log in thread")
        sys.exit()
    logging.info("closing the Log File")
    return True


def stop_logging(self):
    global event_closer
    event_closer.set()
    return True


class SerialPort(object):
    def __init__(self) -> None:
        self.port = "/dev/ttyACM1"
        self.baudrate = 115200
        self.timeout = 60

    def create_serial(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            if not ser.is_open:
                logging.info("Opening Serial Port")
                ser.open()
            return ser
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def write_cmd(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except serial.SerialException:
            raise signals.TestAbortAll("Failed to Reset the device")

        cmd = b'matter device factoryreset\n'

        for i in range(1, 4):
            logging.info("resetting nordic matter device")
            ser.write(cmd)
            time.sleep(2)

        ser.close()
