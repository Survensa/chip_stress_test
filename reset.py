from mobly import asserts, base_test, signals, utils
import logging
from fabric import Connection
from invoke import UnexpectedExit
import invoke.exceptions
from abc import ABC, abstractmethod
from config import rpi_config
import threading
import subprocess
import time
import os
import serial
import sys
import config


class Reset(ABC):

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def factory_reset(self):
        pass

    @abstractmethod
    def advertise(self):
        pass

    @abstractmethod
    def start_logging(self):
        pass

    @abstractmethod
    def stop_logging(self):
        pass


class Rpi(Reset):
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
                    kill_command = f"kill -9 {pid}"
                    ssh.run(kill_command)

        logging.info("Example App has been closed")

        ssh.close()

        if i:
            thread = threading.Thread(target=self.advertise)
            thread.start()

        time.sleep(10)

    def advertise(self):

        logging.info("advertising the DUT")

        data = rpi_config()

        ssh = Connection(host=data.host, user=data.username, connect_kwargs={"password": data.password})
        path = data.path
        ssh.run('rm -rf /tmp/chip_*')

        try:
            log = ssh.run('cd ' + path + ' && ' + data.command, warn=True, hide=True, pty=False)
        except UnexpectedExit as e:
            if e.result.exited == -1:
                None
            else:
                raise

        self.start_logging(log)
        ssh.close()
        logging.info('Iteration has been completed')

        return True

    def start_logging(self, log):

        log_file = "TC_PairUnpair_log.txt"

        if Rpi.count:
            with open(log_file, 'a') as l:
                l.write(f" \n\n  Dut log of {Rpi.count} iteration \n")
                l.write(log.stdout)

        Rpi.count += 1

        return True

    def stop_logging(self):

        # As we are killing the example while factory reset this will stop the logging process
        return (self.factory_reset(0))


class CustomDut(Reset):
    """This class will be overriden by the user for different devices
    the user will have to populate these fucntions when writing the test case
    each dut will have its own method for reset which they have implemet themselves
    the code below is written as an example for demo puposes
    """

    def reboot(self):
        pass

    def factory_reset(self, i):
        pass

    def advertise(self):
        pass

    def start_logging(self, log):
        pass

    def stop_logging(self):
        pass


def test_start():
    log_file = "TC_PairUnpair_log.txt"
    user_interaction_start()
    copy_argv = sys.argv
    copy_argv.append("--commissioning-method")
    copy_argv.append(config.commissioning_metod)
    sys.argv = copy_argv
    if os.path.exists(log_file):
        os.remove(log_file)

    if config.platform_execution == 'rpi':
        logging.info("advertising the dut")
        thread = threading.Thread(target=Rpi().advertise)
        thread.start()
        time.sleep(5)

    elif config.platform_execution == 'CustomDut':
        thread = threading.Thread(target=CustomDut().advertise)
        thread.start()
        # CustomDut().advertise
        time.sleep(5)

    return True


def test_stop(platform):
    if platform == 'rpi':
        Rpi().stop_logging()

    elif platform == 'thread':
        CustomDut().stop_logging()


def reset(platform, i):
    if platform == "rpi":
        Rpi().factory_reset(i)
        time.sleep(2)

    elif platform == 'CustomDut':
        logging.info("CUSTOM DUT device is going to be reset")
        CustomDut().factory_reset(i)
    return True


def platform_setter():
    platform_set = input("\n---------Select Desired platform for DUT to run-------\
                       \n\t\t1 for RPI which is aka raspberrypi\
                       \n\t\t2 for Custom DUT Device\n")
    if platform_set == "1" or platform_set == '2':
        if platform_set == '1':
            config.platform_execution = 'rpi'
        else:
            path_of_file = input("Provide Absolute path for the python file")
            if os.path.exists(path_of_file):
                config.platform_execution = "CustomDut"
                sys.path.insert(1, path_of_file)
                import override
                CustomDut.factory_reset = override.factory_reset
                CustomDut.advertise = override.advertise
                CustomDut.start_logging = override.start_logging
                CustomDut.stop_logging = override.stop_logging
    else:
        print("\n!!!!!!INAVLID OPTION SELECTED, restarting platform selection process!!!!!!!!!\n")
        platform_setter()


def iteration_setter():
    iteration_number = input("\n----Enter the number of iterations, ONLY INTEGERS ARE ACCEPTED-------\n")
    if iteration_number.isdecimal():
        config.iteration_number = iteration_number
    else:
        print("\n!!!!!!!INTEGER NUMBER NOT RECEIEVED, restarting iteration number setting process!!!!!!!!\n")
        iteration_setter()


def rpi_username():
    username = input(
        "\n----Enter  Username for RPI PLATFORM if no data is entered then default username '{}' is used-------\n".format(
            config.rpi_user))
    if username != '':
        config.rpi_user = username


def rpi_password():
    password = input(
        "\n----Enter  Password for RPI PLATFORM if no data is entered then default password '{}' is used-------\n".format(
            config.rpi_password))
    if password != '':
        config.rpi_password = password


def rpi_hostname():
    hostname = input(
        "\n----Enter  Host Address for RPI PLATFORM if no data is entered then default host address '{}' is used-------\n".format(
            config.rpi_host))
    if hostname != '':
        config.rpi_user = hostname


def advertise_dut_func():
    command = input(
        "\n----Enter  Command to start DUT Device if no data is entered the default commad used will be '{}'-------\n".format(
            config.rpi_cmd))
    if command != '':
        config.rpi_cmd = command


def connection_timeout_setter():
    timeout = input(
        "\n----Enter the timeout for DUT Connection in seconds not greater than 60-------\n".format(config.rpi_cmd))
    if timeout.isdecimal():
        if int(timeout) <= 60 and int(timeout) > 0:
            config.dut_connection_timeout = int(timeout)
        else:
            print("\n!!!!!!!!!!!Enter the DUT Connection timeout less than or equal to 60!!!!!!\n")
            connection_timeout_setter()
    else:
        print("!!!!!!The value recieved is not acceptable!!!!!!")
        connection_timeout_setter()


def execution_mode_test_case():
    execution_mode = input("\n----Select the options below for execution mode------\
                         \n\t\t1 for Full execution mode where if any test case fails the execution will not stop\
                         \n\t\t2 for Partial execution mode where in failure of any test case will result in the exit of the script \n")
    if execution_mode == "1" or execution_mode == "2":
        config.execution_mode_full = False if execution_mode == "2" else True
    else:
        print("\n!!!!!!INVALID OPTION SELECTED!!!!!!\n")
        execution_mode_test_case()


def advertise_path():
    path = input("\n--------Enter the Absolute path where the DUT Script is located------\n")
    if path != '':
        config.rpi_path = path
    else:
        print("\n!!!!!! This option cannot be left Blank !!!!!!\n")
        advertise_path()


def commissioning_method():
    comm_method = input("\n-----Select the appropriate option for commissioning_method-----\
                      \n\t\t1 for 'on-network'\
                      \n\t\t2 for 'ble-wifi'\
                      \n\t\t3 for 'ble-thread'\n")
    if comm_method in ["1", "2", "3"]:
        if comm_method == "1":
            config.commissioning_metod = 'on-network'
        elif comm_method == "2":
            config.commissioning_metod = 'ble-wifi'
        else:
            config.commissioning_metod = 'ble-thread'
    else:
        print("\n!!!!!! INVALID OPTION SELECTED !!!!!!\n")
        commissioning_method()


def display_oprtions(option_selected):
    rpi_options_data = "\n\t\t RPI Username '{}'\
            \n\t\t RPI Hostname '{}'\
            \n\t\t RPI Password '{}'\
            \n\t\t Absoulte Path To Advertise the DUT '{}'\
            \n\t\t Command to Advertise the DUT '{}'".format(
        config.rpi_user, config.rpi_host,
        config.rpi_password, config.rpi_path,
        config.rpi_cmd) if config.platform_execution == 'rpi' else "\n"
    print("You have Selected {} The Script will continue execution with the following configurations \n \
                         \n\t\t Platform Selected is '{}'\
                         \n\t\t Number Of Iterations '{}'\
                         \n\t\t Connection Timeout Between DUT and Commissioner '{}'\
                         \n\t\t Execution Mode is Set to '{}' {}\
                         \n\t\t Commissioning Method is '{}'\n\
                         ".format(option_selected,config.platform_execution, config.iteration_number, config.dut_connection_timeout,
                                  "Full execution mode" if config.execution_mode_full else "Partial execution mode",
                                  "Meaning The Script will Continue to execute even if one of the iteration Fails" if config.execution_mode_full else "Meaning The Script will Exit the execution even if one of the iteration Fails",
                                  config.commissioning_metod) + rpi_options_data)
    option = input("\n----Press 1 to continue execution and 2 start from beginning-----\n")
    if option in ["1", "2"]:
        if option == "1":
            pass
        if option == "2":
            custom_mode()
    else:
        print("\n!!!!!! INVALID OPTION SELECTED !!!!!!\n")
        display_oprtions()


def custom_mode():
    platform_setter()
    iteration_setter()
    if config.platform_execution == 'rpi':
        rpi_username()
        rpi_password()
        rpi_hostname()
        advertise_dut_func()
        advertise_path()
    connection_timeout_setter()
    execution_mode_test_case()
    commissioning_method()
    display_oprtions(option_selected="Custom Dut")


def user_interaction_start():
    print("\n++++++ WELCOME TO AUTOMATION SCRIPT OF PAIR AND UNPAIR DUT +++++++\n \tKindly Select Desired options \n")
    run_full_script = input(
        "the Script has Two modes 'Default Mode' and 'Custom Mode'. Press \n\t\t1 for Default Mode \n\t\t2 for User Mode Execution\n\t\t3 for using Yaml File as input\n")
    if run_full_script in ["1","2","3"]:
        if run_full_script == "1":
            print("You have Selected Default Mode The Script will contibue execution with the following configurations \n \
                         \n\t\t Platform Execution Mode '{}'\
                         \n\t\t Number Of Iterations '{}'\
                         \n\t\t RPI Username '{}'\
                         \n\t\t RPI Hostname '{}'\
                         \n\t\t RPI Password '{}'\
                         \n\t\t Path To Advertise the DUT '{}'\
                         \n\t\t Command to Advertise the DUT '{}'\
                         \n\t\t Connection Timeout Between DUT and Commissioner '{}'\
                         \n\t\t Execution Mode is Set to '{}' {}\
                         \n\t\t Commissioning Method is '{}'\n\
                         ".format(config.platform_execution, config.iteration_number, config.rpi_user, config.rpi_host,
                                  config.rpi_password, config.rpi_path, config.rpi_cmd, config.dut_connection_timeout,
                                  "Full execution mode" if config.execution_mode_full else "Partial execution mode",
                                  "Meaning The Script will Continue to execute even if one of the iteration Fails" if config.execution_mode_full else "Meaning The Script will Exit the execution even if one of the iteration Fails",
                                  config.commissioning_metod))
            option = input("\n-----Press 1 to continue execution and 2 return back-----\n")
            if option in ["1", "2"]:
                if option == "1":
                    pass
                if option == "2":
                    user_interaction_start()
            else:
                print("\n!!!!!!INVALID OPTION SELECTED!!!!!!\n")
                user_interaction_start()
        elif run_full_script == "2":
            print("You have Selected Custom Mode choose the options Below")
            custom_mode()
        elif run_full_script == "3":
            print("You have selected Yaml as input option")
            config.read_yaml()
            path_of_file=config.path_of_file
            if os.path.exists(path_of_file):
                sys.path.insert(1, path_of_file)
                import override
                CustomDut.factory_reset = override.factory_reset
                CustomDut.advertise = override.advertise
                CustomDut.start_logging = override.start_logging
                CustomDut.stop_logging = override.stop_logging
            else:
                print("File is override file is missing\n Exiting from execution")
                sys.exit(0)
            display_oprtions(option_selected="Yaml Load File")
    else:
        print("\n!!!!!!INVALID OPTION SELECTED!!!!!!\n")
        user_interaction_start()