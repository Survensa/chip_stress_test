from dataclasses import dataclass
import os
import sys
import traceback
from mobly import signals
import yaml

# For Thread skip the following RPI and proceed with Thread from 25 line

platform_execution = "rpi"

dut_connection_timeout = 60

commissioning_metod = "on-network"

iteration_number = 5

path_of_file=None

log_file_path_iterations="/home/ubuntu/log_files"
# Enter the host "ip-address" of your RPI here in rpi_host
rpi_host = "10.42.0.243"

# Enter the username of your RPI here in rpi_user
#  if it is empty the default name "ubuntu" will be assigned
rpi_user = "ubuntu"

# Enter the password of your RPI here in rpi_password
#  if it is empty the default password "raspsberrypi" will be assigned
rpi_password = "raspberrypi"

# Enter the command to advertise the example-app in RPI here in rpi_cmd
#  if it is empty the default all-clusters-app "./chip-all-clusters-app" will be assigned
rpi_cmd = "./chip-all-clusters-app" # application name change var name to

# Enter the path to advertise the example-app in RPI here in rpi_cmd
#  if it is empty the default path "/home/ubuntu/apps" will be assigned
rpi_path = "/home/ubuntu/matter_DUT/connectedhomeip/examples/all-clusters-app/linux/out/all-clusters-app"

# For RPI the below nrf can be skipped

# Enter the "ip-address" of your system (where the thread dk is connected) here in nrf_host
#  if it is empty the thread dk should be connected in controller
nrf_host = ""

# Enter the username of your system (where the thread dk is connected) here in nrf_user
#  if it is empty the default name "ubuntu" will be assigned
nrf_user = ""

# Enter the password of your  system (where the thread dk is connected) here in nrf_password
#  if it is empty the default password "raspsberrypi" will be assigned
nrf_password = ""

# Enter the port in your  system (where the thread dk is connected) here in nrf_port
#  if it is empty the default port "/dev/ttyACM0" will be assigned
nrf_port = "/dev/ttyACM1"

# Enter the baudrate in your  device (where the thread dk is communicate) here in nrf_baudrate
#  if it is None the default daultrate "115200" will be assigned
nrf_baudrate = None

execution_mode_full = True


@dataclass
class Rpi_config:
    host: str = None
    username: str = "ubuntu"
    password: str = "raspberrypi"
    path: str = "home/ubuntu/matter_DUT/connectedhomeip/examples/all-clusters-app/linux/out/all-clusters-app"
    command: str = "./chip-all-clusters-app"


def rpi_config():
    config = Rpi_config()

    if rpi_host != "":
        config.host = rpi_host

    else:
        raise signals.TestAbortAll("Missing RPI host for factoryrest, Update the config.py")

    if rpi_user != "":
        config.username = rpi_user

    if rpi_password != "":
        config.password = rpi_password

    if rpi_path != "":
        config.path = rpi_path

    if rpi_cmd != "":
        config.command = rpi_cmd

    return config
# TO BE REMOVED 
# Sample Yaml dictionary 
# {'rpi_config': {'rpi_hostname': '10.42.0.243', 'rpi_DUT_path': '/home/ubuntu/matter_DUT/connectedhomeip/examples/all-clusters-app/linux/out/all-clusters-app',
#                  'rpi_command': './chip-all-clusters-app', 'rpi_user': 'ubuntu', 
#                  'rpi_password': 'raspberrypi'}, 
#                  'general_configs': {'platform_execution': 'CustomDUT',
#                                       'dut_connection_timeout': 60,
#                                       'commissioning_metod': 'on-network', 'iteration_number': 5, 
#                                       'execution_mode_full': True}}
def log_path_add_args(path):
    args=sys.argv
    args.append("--logs-path")
    args.append(path)
def read_yaml(yaml_file="configFile.yaml"):
    print("\n \t\t Started to Load Yaml File \n")
    try:
        if not os.path.exists(yaml_file):
            raise Exception("The Path {} Does not exist".format(yaml_file))
        fp=open(yaml_file)
        data_from_yaml=yaml.load(fp,Loader=yaml.FullLoader)
        fp.close()
        global platform_execution,dut_connection_timeout,\
        commissioning_metod,iteration_number,log_file_path_iterations,\
        execution_mode_full, rpi_host,rpi_user,rpi_password,rpi_cmd,rpi_path,path_of_file
        platform_execution = data_from_yaml['general_configs']['platform_execution']
        dut_connection_timeout = data_from_yaml['general_configs']['dut_connection_timeout']
        commissioning_metod = data_from_yaml['general_configs']["commissioning_metod"]
        iteration_number = data_from_yaml['general_configs']["iteration_number"]
        path_of_file=data_from_yaml['general_configs']['dut_controller_file_path']
        log_file_path_conf=data_from_yaml['general_configs']["logFilePath"]
        if log_file_path_conf is None :
            log_file_path_iterations = os.getcwd()+"/Iteration_logs" 
            log_file_path_general=os.getcwd()+"/general_logs"
            if not os.path.exists(log_file_path_general):
                os.mkdir(log_file_path_general)
            if not os.path.exists(log_file_path_iterations):
                os.mkdir(log_file_path_iterations)
            log_path_add_args(log_file_path_general)
        else:
            path_of_file=data_from_yaml['general_configs']["logFilePath"]
            if not os.path.exists(log_file_path_iterations):
                raise Exception("The Path {} Does not exist".format(path_of_file))
            else:
                log_file_path_iterations = path_of_file+"/Iteration_logs"
                log_file_path_general=path_of_file+"/general_logs"
                log_path_add_args(log_file_path_general)

        execution_mode_full=data_from_yaml['general_configs']["execution_mode_full"]
        if platform_execution=="rpi":
            rpi_host = data_from_yaml['rpi_config']['rpi_hostname']
            rpi_user = data_from_yaml['rpi_config']['rpi_user']
            rpi_password = data_from_yaml['rpi_config']['rpi_password']
            rpi_cmd = data_from_yaml['rpi_config']['rpi_command']
            rpi_path = data_from_yaml['rpi_config']['rpi_DUT_path']
    except Exception as e:
        print("\nError has occured when loading file following is the Reason:")
        print(e)
        traceback.print_exc()
        print("existing from script")
        sys.exit(0)
        
    print("\t\tFinished Loading Yaml file\n")
