# Project Setup

This README provides comprehensive instructions for setting up and running the Python environment for the project. Below are the steps to follow:

## 🛠️ Environment Setup

### Cloning the Repository and Environment Activation

Clone the repository and activate the environment by executing the following commands:

```bash
git clone https://github.com/project-chip/connectedhomeip.git
cd connectedhomeip
source scripts/bootstrap.sh
source scripts/activate.sh
scripts/build_python.sh -m platform -d true -i <name_of_python_environment>
source <name_of_python_environment>/bin/activate
```

After activating the environment, from root directory of this project copy the contents to `<path_to_cloned_repo>/connectedhomeip/src/python_testing` and navigate to this path.

You can use commands like ```cp <path_to_this_project>/Functional/* <path_to_cloned_repo>/connectedhomeip/src/python_testing``` , and navigate by ```cd <path_to_cloned_repo>/connectedhomeip/src/python_testing``` 

### Library Installation

To install the necessary libraries, run:

```bash
python setup.py install
```

# 🏃 Running Test Script Reliability

The reliability scripts are located at `<path_to_cloned_repo>/connectedhomeip/src/python_testing/matter_qa/scripts/reliability_scripts`. 

## ConFig File Setup

Each script requires configurations detailed in `configFile.yaml` located at `<path_to_cloned_repo>/connectedhomeip/src/python_testing/matter_qa/configs/`.



#### ✏️ General Configs


| Parameter                  | Type      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|:---------------------------|:----------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `platform_execution`       | `string`  | DUT Platform Execution can be controlled here. If the user wants to use 'rapsberrypi' device as a DUT use ```rpi```,enabling this will make the script use the ```rpi_config``` and interact with the matter application present in the raspberrypi. Any other String used in this option will make the script use <br> the user's dut interaction script, which will be respective user's DUT interaction class which they will have to implement and use. |
| `module`                   | `string`  | here the user will either provide python based import like ```matter_qa.library.platform.raspberrypi``` or full path to dut_interaction python script                                                                                                                                                                                                                                                                                                       |
| `number_of_iterations`     | `integer` | will be used by the script to run n number of times, as example take the "TC_Pair.py" script, if we want to pair and unpair from the device n number of time we need pass integers here to run n number of times.                                                                                                                                                                                                                                           |
| `analytical_parameters`    | `array`   | Matter devices have certain diagnostics clusters which can be queried for analytics purposes, here user will need to provide which attributes of the ```SoftwareDiagnostics``` cluster to monitor.                                                                                                                                                                                                                                                          |

#### ✏️ Raspberry-pi config(rpi_config)

| Parameter      | Type     | Description                                                                            |
|:---------------|:---------|:---------------------------------------------------------------------------------------|
| `rpi_hotsname` | `string` | Here user will provide the raspberrypi <br/> Ip adderess                               |
| `rpi_username` | `string` | the user name of the Raspberrypi                                                       |
| `matter_app`   | `string` | full path and script name of the matter cluster application along with command options |


#### ✏️ Nordic serial config(nordic_config)
This option will be used by the `nordic.py` script to interact with Nordic dev board

| Parameter         | Type      | Description                                                                                |
|:------------------|:----------|:-------------------------------------------------------------------------------------------|
| `serial_port`     | `string`  | serial port path,example; for linux systems it will be `/dev/tty/ACM0`, for windows `COM1` |
| `serial_baudrate` | `integer` | Baudrate number                                                                            |
| `serial_timeout`  | `integer` | timeout for interacting with the nordic dev board                                          |

### ℹ️ About Test Script 'TC_Pair.py'

The scripts in the repository are used to pair and unpair with DUT multiple times. Currently, two simulated modes of DUT are assumed: Raspberry Pi and nRf52840-DK development thread board. The Raspberry Pi mode will take an SSH session, bring up the sample app perform test operations and kill the sample app once done. 


### Raspberry Pi

Execute the following command to run the script, where inputs are read from the project's config file:

```bash
python3 TC_Pair.py --discriminator 3790 --passcode 20202021 --storage-path admin_storage.json --timeout 900 --commissioning-method on-network --logs-path <path/to/store/execution/logs> --reliability-tests-arg <path/to/configFile.yaml> --trace-to json:log
```
#### ℹ️ _Important Note_
The scripts will expect ```--logs-path``` argument for storing the execution logs to user's desired directory, if not given then it will store in ```/tmp/``` directory

When running the code for 'ble-wifi' commissioning method must be set to 'ble-wifi' and use the command below

```bash
python3 TC_Pair.py --discriminator 3790 --passcode 20202021 --storage-path admin_storage.json --timeout 900 --commissioning-method ble-wifi --logs-path <path/to/store/execution/logs> --reliability-tests-arg <path/to/configFile.yaml> --trace-to json:log --wifi-ssid <wifi-name> --wifi-passphrase <wifi-password>
```
### Nordic Thread

For Nordic Thread, use the following command:

```bash
python3 TC_Pair.py --discriminator 3790 --passcode 20202021 --storage-path admin_storage.json --timeout 900 --commissioning-method ble-thread --logs-path <path/to/store/execution/logs> --reliability-tests-arg <path/to/configFile.yaml> --trace-to json:log --ble-interface-id 0  --thread-dataset-hex <hex-generated-data>
```

# LOG Display Web App


## 🚀 Execution Steps

Edit the config file located at `<path_to_cloned_repo>/connectedhomeip/src/python_testing/logDisplayWebApp/config/config.yaml` with desired configurations.

To run the application, navigate to `<path_to_cloned_repo>/connectedhomeip/src/python_testing/logDisplayWebApp` and execute:

```bash
python LogDisplay.py
```

Alternatively, pass a config file to the application:

```bash
python LogDisplay.py --config <path_to_config_file>/config.yaml
```

Access the homepage of the app at `http://host-name:port/home` once the app starts.


## 🖥️ About the Application

The LOG Display Web App serves as a visualization tool for users to check the pass and fail status of iterations. It reads a config file from the project directory for configurations.

### Features

- Displays all folders present in the LOG Directory.
- Allows downloading folders in 'zip' format or deleting directories.<br><br>
  ![Alt Text](images/readme/home_page.png)<br><br>
- Provides tables with iteration summary, test result, execution time, and options to view DUT logs.
- Offers pagination for ease of data viewing.<br><br>
  ![Alt Text](images/readme/summary_page.png)<br><br>
- Includes analytics feature with line graphs for visualization.<br><br>
  ![Alt Text](images/readme/Enlarged_analytics_graph.png)<br><br>
- Supports comparison of analytics parameters against iteration numbers.<br><br>
  ![Alt Text](images/readme/compare_api.png)<br><br>


