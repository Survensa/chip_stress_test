import datetime
import logging
import os.path
import threading
import time
import traceback

from fabric import Connection
from invoke import UnexpectedExit
from Matter_QA.Library.BaseTestCases.BaseDUTNodeClass import BaseDutNodeClass, BaseNodeDutConfiguration
rpi_count = 1
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

class Raspi(BaseDutNodeClass, BaseNodeDutConfiguration):
    count = 0

    def __init__(self, test_config) -> None:
        super().__init__(test_config)
        self.test_config = test_config

    def reboot_dut(self):
        try:
            ssh = Connection(host=self.test_config["rpi_config"]["rpi_hostname"],
                             user=self.test_config["rpi_config"]["rpi_username"],
                             connect_kwargs={"password": self.test_config["rpi_config"]["rpi_password"]})
            reboot_command = f"sudo reboot"
            ssh.run(reboot_command)
            return True
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            return True

    def factory_reset_dut(self, stop_reset):
        try:
            logger.info("Starting to Reset the DUT")
            ssh = Connection(host=self.test_config["rpi_config"]["rpi_hostname"],
                             user=self.test_config["rpi_config"]["rpi_username"],
                             connect_kwargs={"password": self.test_config["rpi_config"]["rpi_password"]})
            # Executing the  'ps aux | grep process_name' command to find the PID value to kill
            command = f'ps aux | grep "{self.test_config["rpi_config"]["app_config"]["matter_app"]}"'
            pid_val = ssh.run(command, hide=True)
            pid_output = pid_val.stdout
            pid_lines = pid_output.split('\n')
            for line in pid_lines:
                try:
                    if self.test_config["rpi_config"]['app_config']['matter_app'] in line:
                        pid = line.split()[1]
                        conformance = line.split()[7]
                        if conformance == 'Ssl':
                            logger.info("About to Terminate the application")
                            logger.info("displaying the pid and process to terminate {}".format(line))
                            kill_command = f"kill {pid}"
                            ssh.run(kill_command)
                except Exception as e:
                    logger.error(e)
                    traceback.print_exc()
                    return True

            logger.info("Example App has been closed")

            ssh.close()

            if not stop_reset:
                thread = threading.Thread(target=self.start_matter_app)
                thread.start()

            time.sleep(10)
        except Exception as e:
            logger.error(e)

    def start_matter_app(self):
        try:
            logger.info("Starting The Matter application")
            ssh = Connection(host=self.test_config["rpi_config"]["rpi_hostname"],
                             user=self.test_config["rpi_config"]["rpi_username"],
                             connect_kwargs={"password": self.test_config["rpi_config"]["rpi_password"]})
            ssh.run('rm -rf /tmp/chip_*')
            command = f'ps aux | grep "{self.test_config["rpi_config"]["app_config"]["matter_app"]}"'
            pid_val = ssh.run(command, hide=True)
            pid_output = pid_val.stdout
            pid_lines = pid_output.split('\n')
            for line in pid_lines:
                try:
                    if self.test_config["rpi_config"]['app_config']['matter_app'] in line:
                        pid = line.split()[1]
                        conformance = line.split()[7]
                        if conformance == 'Ssl':
                            print("the DUT is already working will stop it now")
                            print("displaying the pid of DUT  {}".format(line))
                            kill_command = f"kill {pid}"
                            ssh.run(kill_command)
                except UnexpectedExit as e:
                    logger.error(e)
                    traceback.print_exc()
                    if e.result.exited == -1:
                        pass
                    else:
                        raise
            log = ssh.run(self.test_config["rpi_config"]['app_config']['matter_app'], warn=True, hide=True,
                          pty=False)
            self.start_logging(log)
            ssh.close()
        except UnexpectedExit as e:
            logger.error(e)
            traceback.print_exc()
            if e.result.exited == -1:
                pass
            else:
                raise
        return True

    def start_logging(self, log):
        try:
            global rpi_count
            if self.test_config["current_iteration"] == 0:
                self.test_config["current_iteration"] += 1
            current_dir = self.test_config["iter_logs_dir"]
            log_path = os.path.join(current_dir, str(self.test_config["current_iteration"]))
            if not os.path.exists(log_path):
                os.mkdir(log_path)
            log_file = os.path.join(log_path, "Dut_log_{}_"
                                    .format(str(self.test_config["current_iteration"])) +
                                    str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                    + ".log"
                                    )
            with open(log_file, 'a') as fp:
                fp.write(f" \n\n  Dut log of {rpi_count} iteration \n")
                fp.write(log.stdout)
            rpi_count += 1
            return True
        except Exception as e:
            logger.error(e)
            traceback.print_exc()

    def stop_logging(self):

        # As we are killing the example while factory reset this will stop the logging process
        pass


def create_dut_object(test_config):
    return Raspi(test_config)
