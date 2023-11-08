import datetime
import logging
import os.path
import threading
import time

from fabric import Connection
from invoke import UnexpectedExit
from Matter_QA.Library.BaseTestCases.BaseDUTNodeClass import BaseDutNodeClass, BaseNodeDutConfiguration
rpi_count = 1


class Raspi(BaseDutNodeClass, BaseNodeDutConfiguration):
    count = 0

    def __init__(self, test_config) -> None:
        super().__init__(test_config)
        self.test_config = test_config

    def reboot_dut(self):
        ssh = Connection(host=self.test_config["rpi_config"]["rpi_hostname"],
                         user=self.test_config["rpi_config"]["rpi_username"],
                         connect_kwargs={"password": self.test_config["rpi_config"]["rpi_password"]})
        reboot_command = f"sudo reboot"
        ssh.run(reboot_command)
        return True

    def factory_reset_dut(self, stop_reset):
        logging.info("Starting to Reset the DUT")
        ssh = Connection(host=self.test_config["rpi_config"]["rpi_hostname"],
                         user=self.test_config["rpi_config"]["rpi_username"],
                         connect_kwargs={"password": self.test_config["rpi_config"]["rpi_password"]})
        print("ssh is success")
        # Executing the  'ps aux | grep process_name' command to find the PID value to kill
        command = f"ps aux | grep {self.test_config['app_config']['matter_app']}"
        pid_val = ssh.run(command, hide=True)

        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines:
            if self.test_config['app_config']['matter_app'] in line:
                pid = line.split()[1]
                conformance = line.split()[7]
                if conformance == 'Ssl':
                    logging.info("About to Terminate the application")
                    logging.info("displaying the pid and process to terminate {}".format(line))
                    kill_command = f"kill {pid}"
                    ssh.run(kill_command)

        logging.info("Example App has been closed")

        ssh.close()

        if not stop_reset:
            thread = threading.Thread(target=self.start_matter_app)
            thread.start()

        time.sleep(10)

    def start_matter_app(self):
        logging.info("Starting The Matter application")
        ssh = Connection(host=self.test_config["rpi_config"]["rpi_hostname"],
                         user=self.test_config["rpi_config"]["rpi_username"],
                         connect_kwargs={"password": self.test_config["rpi_config"]["rpi_password"]})
        path = self.test_config["app_config"]["matter_app_path"]
        ssh.run('rm -rf /tmp/chip_*')
        try:
            command = f"ps aux | grep {self.test_config['app_config']['matter_app']}"
            pid_val = ssh.run(command, hide=True)

            pid_output = pid_val.stdout
            pid_lines = pid_output.split('\n')
            for line in pid_lines:
                try:
                    if self.test_config['app_config']['matter_app'] in line:
                        pid = line.split()[1]
                        conformance = line.split()[7]
                        if conformance == 'Ssl':
                            print("the DUT is already working will stop it now")
                            print("displaying the pid of DUT  {}".format(line))
                            kill_command = f"kill {pid}"
                            ssh.run(kill_command)
                except UnexpectedExit as e:
                    if e.result.exited == -1:
                        pass
                    else:
                        raise
            log = ssh.run('cd ' + path + ' && ' + self.test_config['app_config']['matter_app'], warn=True, hide=True,
                          pty=False)
            self.start_logging(log)
            ssh.close()
        except UnexpectedExit as e:
            if e.result.exited == -1:
                pass
            else:
                raise
        return True

    def start_logging(self, log):
        global rpi_count
        date = datetime.datetime.now().isoformat().replace(":","-").replace(".","_")
        dut_log_path = os.path.join(self.test_config["general_configs"]["logFilePath"], "dut_logs")
        if not os.path.exists(dut_log_path):
            os.mkdir(dut_log_path)
        log_file = os.path.join(dut_log_path,
                                "iteration_{}__{}.log".format(rpi_count, date))
        with open(log_file, 'a') as fp:
            fp.write(f" \n\n  Dut log of {rpi_count} iteration \n")
            fp.write(log.stdout)
        rpi_count += 1
        return True

    def stop_logging(self):

        # As we are killing the example while factory reset this will stop the logging process
        pass


def create_dut_object(test_config):
    return Raspi(test_config)
