from dataclasses import dataclass
from mobly import signals

# For Thread skip the following RPI and proceed with Thread from 25 line

platform_execution = "rpi"

dut_connection_timeout = 60

commissioning_metod = "on-network"

iteration_number = 5
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
rpi_cmd = "./chip-all-clusters-app"

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
