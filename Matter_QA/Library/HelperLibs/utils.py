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
import importlib.util
import io
import json
import logging
import os
import signal
import sys
import traceback

import yaml

from Matter_QA.Library.Platform.raspberrypi import raspi

_DEFAULT_CONFIG_FILE = os.getcwd()


class CommissionTimeoutError(Exception):
    pass


class TestConfig(object):
    def __init__(self, config_dict):
        for key, value in config_dict.items():
            if isinstance(value, dict):
                setattr(self, key, TestConfig(value))
            else:
                setattr(self, key, value)


def convert_args_dict(args: list):
    """
    This function is used to convert arguments passed via cmd line to dict format
    """
    keys = []
    values = []
    for arg in args:
        if "--" in arg and arg.startswith("--"):
            keys.append(arg)
        else:
            values.append(arg)
    return dict(zip(keys, values))


def timeouterror(signum, frame):
    raise CommissionTimeoutError("timed out, Failed to commission the dut")


def timer(function):
    def wrapper(*args, **kwargs):
        # Set the alarm for the timeout
        timeout = kwargs.pop('timeout', 60)
        signal.signal(signal.SIGALRM, timeouterror)
        signal.alarm(timeout)
        try:
            result = function(*args, **kwargs)
        finally:
            # Cancel the alarm after the function finishes
            signal.alarm(0)
        return result

    return wrapper


def dut_object_loader(test_config, dut_objects_list):
    try:

        general_configs = test_config.general_configs
        if test_config.general_configs.platform_execution == 'rpi':
            dut_objects_list.append(raspi.create_dut_object(test_config=test_config))
            raspi.Raspi(test_config=test_config).factory_reset_dut(stop_reset=False)
        else:
            full_path = os.path.join(test_config.general_configs.deviceModules.module_path,
                                     test_config.general_configs.deviceModules.module_name)

            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                logging.error('Error in importing Module! check if file exists')
                sys.exit(0)
            spec = importlib.util.spec_from_file_location(location=full_path,
                                                          name=test_config.general_configs.deviceModules.module_name)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            dut_objects_list.append(module.create_dut_object(test_config))

    except Exception as e:
        logging.error(e)
        traceback.print_exc()


def yaml_config_reader(dict_args):
    try:
        if not os.path.exists(dict_args["--yaml-file"]):
            logging.error("The config file does not exist! exiting now! ")
            sys.exit(0)
        config_yaml_file = dict_args["--yaml-file"]
        with io.open(config_yaml_file, 'r') as f:
            test_config_dict = yaml.safe_load(f)
            test_config = TestConfig(test_config_dict)
        return test_config
    except Exception as e:
        logging.error(e)
        traceback.print_exc()


def default_config_reader():
    try:
        org_dir = os.getcwd()
        os.chdir(os.pardir)
        os.chdir(os.pardir)  # changing directory with platform independency and read configfile from project
        config_yaml_file = os.path.join(os.getcwd(), "Configs", "configFile.yaml")
        if not os.path.exists(config_yaml_file):
            logging.error("The config file does not exist! exiting now! ")
            sys.exit(0)
        with io.open(config_yaml_file, 'r') as f:
            test_config_dict = yaml.safe_load(f)
            test_config = TestConfig(test_config_dict)
        os.chdir(org_dir)
        return test_config
    except Exception as e:
        logging.error(e)
        traceback.print_exc()


def summary_log(test_result: dict, test_config, completed: bool, analytics_json: dict):
    if completed:
        log_data = ("**************Summary of Test Results*******\n\n"
                    "\t\t\tNumber of Iterations  is {}\n\n"
                    "\t\t\tNumber of Passed Iterations  is {}\n\n"
                    "\t\t\tNumber of Failed Iterations  is {}\n\n"
                    "\t\t\tIterations which have failed are {}\n\n"
                    "\t\t\tPlatform used for execution is {}\n\n"
                    "\t\t\tCommissioning method used is {}\n\n"
                    "\t\t\tExecution mode is  {}\n\n".format(test_config.general_configs.iteration_number,
                                                             test_result["Pass Count"],
                                                             test_result["Fail Count"]["Count"],
                                                             test_result["Fail Count"]["Iteration"],
                                                             test_config.general_configs.platform_execution,
                                                             test_config.general_configs.commissioning_method,
                                                             "Full execution Mode" if
                                                             test_config.general_configs.execution_mode_full
                                                             else "Partial Execution Mode",
                                                             ))
        log_file = os.path.join(test_config.iter_logs_dir, "summary.log")
        with open(log_file, "w") as fp:
            fp.write(log_data)
    log_file_json = os.path.join(test_config.iter_logs_dir, "summary.json")
    analytics_json_file = os.path.join(test_config.iter_logs_dir, "analytics.json")

    analytics_json["test_class_name"] = test_config.test_class_name
    analytics_json["iteration_id"] = test_config.iteration_id
    analytics_json.update({"number_of_iterations": test_config.general_configs.iteration_number
    if completed else test_config.current_iteration})

    test_result.update({"platform": test_config.general_configs.platform_execution})
    test_result.update({"number_of_iterations": test_config.general_configs.iteration_number
    if completed else test_config.current_iteration})
    test_result.update({"commissioning_method": test_config.general_configs.commissioning_method})
    test_result.update(
        {"execution_mode": "Full execution Mode" if test_config.general_configs.execution_mode_full
        else "Partial Execution Mode"})
    test_result.update({"analytics_metadata": list(analytics_json["analytics"].keys())})
    with open(log_file_json, "w+") as fp:
        json.dump(test_result, fp, indent=2)
    with open(analytics_json_file, "w+") as fp:
        json.dump(analytics_json, fp, indent=2)
