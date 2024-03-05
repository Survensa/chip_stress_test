import logging

from fabric import Connection
from invoke import UnexpectedExit


class CommonSSH:
    def __init__(self, test_config, logger: logging):
        self.rpi_host = test_config.rpi_config.rpi_hostname
        self.rpi_user = test_config.rpi_config.rpi_username
        self.rpi_password = test_config.rpi_config.rpi_password
        self.matter_app = test_config.rpi_config.app_config.matter_app
        self.connection_object = Connection(host=self.rpi_host, user=self.rpi_user,
                                            connect_kwargs={"password": self.rpi_password})
        self.logger = logger

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
