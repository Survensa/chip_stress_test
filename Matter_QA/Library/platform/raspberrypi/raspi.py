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
import logging
import os.path
import threading
import time
import traceback

from Matter_QA.Library.base_test_classes.base_dut_node_class import BaseDutNodeClass, BaseNodeDutConfiguration
from Matter_QA.Library.helper_libs.common_ssh_control import CommonSSH

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


class Raspi(BaseDutNodeClass, BaseNodeDutConfiguration):
    count = 0

    def __init__(self, test_config) -> None:
        super().__init__(test_config)
        self.test_config = test_config
        self.ssh_session = CommonSSH(test_config=test_config, logger=logger)
        self.matter_app = test_config.rpi_config.app_config.matter_app
        self.ssh_session.open_ssh_connection()

    def reboot_dut(self):
        try:
            reboot_command = f"sudo reboot"
            self.ssh_session.send_command_no_output(reboot_command)
            return True
        except Exception as e:
            logger.error(e, exc_info=True)
            return True

    def factory_reset_dut(self, stop_reset):
        try:
            logger.info("Starting to Reset RPI as the DUT")
            # Executing the  'ps aux | grep process_name' command to find the PID value to kill
            command = f'ps aux | grep "{self.matter_app}"'
            pid_val = self.ssh_session.send_command_receive_output(command)
            pid_output = pid_val.stdout
            pid_lines = pid_output.split('\n')
            for line in pid_lines:
                try:
                    if self.matter_app in line:
                        pid = line.split()[1]
                        if "grep" not in line:
                            logger.info("Displaying the pid and process to terminate {}".format(line))
                            kill_command = f"kill {pid}"
                            self.ssh_session.send_command_no_output(kill_command)
                except Exception as e:
                    logger.error(e)
                    traceback.print_exc()
                    return True

            logger.info("Example App has been closed")
            self.ssh_session.close_ssh_connection()
            if not stop_reset:
                thread = threading.Thread(target=self.start_matter_app)
                thread.start()
            time.sleep(10)
        except Exception as e:
            logger.error(e, exc_info=True)

    def start_matter_app(self):
        try:
            logger.info("Starting The Matter application")
            self.ssh_session.open_ssh_connection()
            self.ssh_session.send_command_no_output('rm -rf /tmp/chip_*')
            command = f'ps aux | grep "{self.matter_app}"'
            pid_val = self.ssh_session.send_command_receive_output(command, hide=True)
            pid_output = pid_val.stdout
            pid_lines = pid_output.split('\n')
            for line in pid_lines:
                try:
                    if self.matter_app in line:
                        pid = line.split()[1]
                        if "grep" not in line:
                            logger.info("Displaying the pid and process to terminate {}".format(line))
                            kill_command = f"kill {pid}"
                            self.ssh_session.send_command_no_output(kill_command)
                except Exception as e:
                    logger.error(e)
                    traceback.print_exc()
                    return True

            log = self.ssh_session.send_command_receive_output(self.matter_app, warn=True, hide=True, pty=False)
            self.start_logging(log)
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
        return True

    def start_logging(self, log):
        try:
            if self.test_config.current_iteration == 0:
                self.test_config.current_iteration += 1
            current_dir = self.test_config.iter_logs_dir
            log_path = os.path.join(current_dir, str(self.test_config.current_iteration))
            if not os.path.exists(log_path):
                os.mkdir(log_path)
            log_file = os.path.join(log_path, "Dut_log_{}_"
                                    .format(str(self.test_config.current_iteration)) +
                                    str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                    + ".log"
                                    )
            with open(log_file, 'a') as fp:
                fp.write(f" \n\n  Dut log of {self.test_config.current_iteration} iteration \n")
                fp.write(log.stdout)
            return True
        except Exception as e:
            logger.error(e, exc_info=True)

    def stop_logging(self):

        # As we are killing the example while factory reset this will stop the logging process
        pass

    def pre_iteration_loop(self):
        pass

    def post_iteration_loop(self):
        pass


def create_dut_object(test_config):
    return Raspi(test_config)
