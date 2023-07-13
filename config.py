from dataclasses import dataclass
from mobly import  signals
# For Thread skip the following RPI and proceed with Thread from 25 line 


#Enter the host "ip-address" of your RPI here in rpi_host
rpi_host = "192.168.4.218"

#Enter the username of your RPI here in rpi_user
#  if it is empty the default name "ubuntu" will be assigned
rpi_user = ""

#Enter the password of your RPI here in rpi_password
#  if it is empty the default password "raspsberrypi" will be assigned
rpi_password = ""

#Enter the command to advertise the example-app in RPI here in rpi_cmd
#  if it is empty the default all-clusters-app "./chip-all-clusters-app" will be assigned
rpi_cmd = ""

#Enter the path to advertise the example-app in RPI here in rpi_cmd
#  if it is empty the default path "/home/ubuntu/apps" will be assigned
rpi_path = ""

#For RPI the below nrf can be skipped

#Enter the "ip-address" of your system (where the thread dk is connected) here in nrf_host
#  if it is empty the thread dk should be connected in controller
nrf_host = "192.168.4.122"

#Enter the username of your system (where the thread dk is connected) here in nrf_user
#  if it is empty the default name "ubuntu" will be assigned
nrf_user = ""

#Enter the password of your  system (where the thread dk is connected) here in nrf_password
#  if it is empty the default password "raspsberrypi" will be assigned
nrf_password = ""

#Enter the port in your  system (where the thread dk is connected) here in nrf_port
#  if it is empty the default port "/dev/ttyACM0" will be assigned
nrf_port = ""

@dataclass
class Rpi_config:
    host : str = None
    username: str = "ubuntu"
    password: str = "raspberrypi"
    path: str = "/home/ubuntu/apps"
    command: str  = "./chip-all-clusters-app"


@dataclass
class Thread_config: 
    host : str = None
    username: str = "ubuntu"
    password: str = "raspberrypi"
    port: str = "/dev/ttyACM0"


def rpi_config():

    config = Rpi_config()

    if rpi_host != "":
        config.host = rpi_host
    
    else:
        raise signals.TestAbortAll("Missing RPI host for factoryrest, Update the config.py")

    if rpi_user != "":
        config.username = rpi_user

    if rpi_password != "":
        config.username = rpi_password
    
    if rpi_path != "":
        config.username = rpi_path
    
    if rpi_cmd != "":
        config.username = rpi_cmd
    

    return config


def thread_config():

    config = Thread_config()

    if nrf_host == "" :
        return False
    
    else:

        config.host = nrf_host

    if nrf_user != "":
        config.username = nrf_user

    if nrf_password != "":
        config.password = nrf_password

    if nrf_port != "":
        config.port = nrf_port

    return config





