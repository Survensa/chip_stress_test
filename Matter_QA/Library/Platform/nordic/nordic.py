import datetime
import traceback
import serial
import time
import logging
import os
from threading import Event, Thread
import sys
from mobly import signals
from Matter_QA.Library.BaseTestCases.BaseDUTNodeClass import BaseDutNodeClass, BaseNodeDutConfiguration

event_closer = Event()


class NordicDut(BaseDutNodeClass, BaseNodeDutConfiguration):
    def __init__(self, test_config) -> None:
        super().__init__(test_config)
        self.test_config = test_config

    def reboot_dut(self):
        pass

    def factory_reset_dut(self, stop_reset: bool):
        if not stop_reset:
            # self.stop_logging()
            SerialPort().write_cmd()
            return True
        else:
            self.start_matter_app()
            logging.info("completed advertising of DUT")
            return True

    def start_matter_app(self):
        SerialPort().write_cmd()
        time.sleep(2)
        return True

    def start_logging(self, log=None) -> bool:
        global event_closer
        if self.test_config["current_iteration"] == 0:
            self.test_config["current_iteration"] += 1
        ser = SerialPort().create_serial()
        if ser.is_open:
            while ser.is_open:
                try:
                    current_dir = self.test_config["iter_logs_dir"]
                    log_path = os.path.join(current_dir, str(self.test_config["current_iteration"]))
                    if not os.path.exists(log_path):
                        os.mkdir(log_path)
                    log_file = os.path.join(log_path, "Dut_log_{}_"
                                            .format(str(self.test_config["current_iteration"])) +
                                            str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                            + ".log"
                                            )
                    logging.info("started to read buffer")
                    data = ser.read_until(b'Done\r\r\n').decode()
                    logging.info("completed read from buffer")
                    if data == '':
                        logging.info("data not present in buffer breaking from read loop")
                        break
                    with open(log_file,'w') as fp:
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


def create_dut_object(test_config):
    dut_obj = NordicDut(test_config=test_config)
    thread = Thread(target=dut_obj.start_logging)
    thread.start()
    dut_obj.factory_reset_dut(stop_reset=False)
    return dut_obj
