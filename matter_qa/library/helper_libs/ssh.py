import logging
import sys
import os
from fabric import Connection
from invoke import UnexpectedExit

log = logging.getLogger("ssh")

class SSH:
    def __init__(self, ssh_config):
  
        self.rpi_host = ssh_config.hostname
        self.rpi_user = ssh_config.username
        self.rpi_password = ssh_config.password

        try:
            self.connection_object = Connection(host=self.rpi_host, user=self.rpi_user,
                                            connect_kwargs={"password": self.rpi_password})
        except Exception as e:
            log.error("could not establish SSH to raspi DUT: {e}")
            sys.exit(1)

    def send_command_receive_output(self, command, **kwargs):
        try:
            output = self.connection_object.run(command=command, **kwargs)
            return output
        except (Exception, UnexpectedExit) as e:
            self.logger.error(str(e), exc_info=True)

    def send_command_no_output(self, command, **kwargs):
        try:
            self.connection_object.run(command, **kwargs)
        except (Exception, UnexpectedExit) as e:
            self.logger.error(str(e), exc_info=True)

    def open_ssh_connection(self):
        self.connection_object.open()

    def close_ssh_connection(self):
        self.connection_object.close()