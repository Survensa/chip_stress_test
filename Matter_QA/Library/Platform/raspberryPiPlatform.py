import logging
import threading
import time
import traceback

from fabric import Connection
from invoke import UnexpectedExit
from Matter_QA.Configs import initializer

from Matter_QA.Configs.initializer import rpi_config
from Matter_QA.Library.Platform.BaseDUT import BaseDutClass


class Rpi(BaseDutClass):
    count = 0

    def reboot(self):
        data = rpi_config()

        ssh = Connection(host=data.host, user=data.username, connect_kwargs={"password": data.password})

        reboot_command = f"sudo reboot"

        ssh.run(reboot_command)

        return True

    def factory_reset(self, i):

        data = rpi_config()

        ssh = Connection(host=data.host, user=data.username, connect_kwargs={"password": data.password})
        print("ssh is success")

        # Executing the  'ps aux | grep process_name' command to find the PID value to kill
        command = f"ps aux | grep {data.command}"
        pid_val = ssh.run(command, hide=True)

        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines:
            if data.command in line:
                pid = line.split()[1]
                conformance = line.split()[7]
                if conformance == 'Ssl':
                    logging.info("About to Terminate the application")
                    logging.info("displaying the pid and process to terminate {}".format(line))
                    kill_command = f"kill {pid}"
                    ssh.run(kill_command)

        logging.info("Example App has been closed")

        ssh.close()

        if i:
            thread = threading.Thread(target=self.advertise)
            thread.start()

        time.sleep(10)

    def advertise(self):

        print("advertising the DUT")

        data = rpi_config()

        ssh = Connection(host=data.host, user=data.username, connect_kwargs={"password": data.password})
        path = data.path
        ssh.run('rm -rf /tmp/chip_*')

        try:
            command = f"ps aux | grep {data.command}"
            pid_val = ssh.run(command, hide=True)

            pid_output = pid_val.stdout
            pid_lines = pid_output.split('\n')
            for line in pid_lines:
                try:
                    if data.command in line:
                        pid = line.split()[1]
                        conformance = line.split()[7]
                        if conformance == 'Ssl':
                            print("the DUT is already working will stop it now")
                            print("displaying the pid of DUT  {}".format(line))
                            kill_command = f"kill {pid}"
                            ssh.run(kill_command)
                except UnexpectedExit as e:
                    if e.result.exited == -1:
                        None
                    else:
                        raise
            log = ssh.run('cd ' + path + ' && ' + data.command, warn=True, hide=True, pty=False)
            self.start_logging(log)
            ssh.close()
        except UnexpectedExit as e:
            if e.result.exited == -1:
                None
            else:
                raise
        return True

    def start_logging(self, log):
        try:
            log_file = initializer.dut_log_path+"/TC_PairUnpair_log.txt"

            if Rpi.count:
                with open(log_file, 'a') as l:
                    l.write(f" \n\n  Dut log of {Rpi.count} iteration \n")
                    l.write(log.stdout)
                    logging.info("Written logs to file at {}".format(log_file))

            Rpi.count += 1

            return True
        except Exception as e:
            logging.error(e)
            traceback.print_exc()

    def stop_logging(self):

        # As we are killing the example while factory reset this will stop the logging process
        return self.factory_reset(0)
