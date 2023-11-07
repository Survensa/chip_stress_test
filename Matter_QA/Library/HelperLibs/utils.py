import datetime
import logging
import os
import re
import signal
import sys

from Matter_QA.Configs import initializer
#TODO
#from Matter_QA.Library.Platform import CustomDut


class CommissionTimeoutError(Exception):
    pass


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


def custom_dut_class_override():
    """This is crucial function in the script, this script will override the CustomDut class.
        It will check for the override.py file in the system and import it.
        the imported python file will be used to override the CustomDut class"""
    path_of_file = initializer.path_of_file
    if os.path.exists(path_of_file) :
        sys.path.insert(1, path_of_file)
        import override
        CustomDut.factory_reset = override.factory_reset
        CustomDut.advertise = override.advertise
        CustomDut.start_logging = override.start_logging
        CustomDut.stop_logging = override.stop_logging
    else:
        print("File is override file is missing\n Exiting from execution")
        sys.exit(0)


def timeouterror(signum, frame):
    raise CommissionTimeoutError("timed out, Failed to commission the dut")


def log_file_finder():
    dict_args = convert_args_dict(sys.argv[1:])
    log_file_path = dict_args["--logs-path"]
    dirs = os.listdir(log_file_path + "/MatterTest")
    logging.info("files present in {}".format(dirs))
    file_info_dict = {}
    for i in dirs:
        file_info_dict[os.stat(log_file_path + "/MatterTest/" + i).st_mtime] = i
    keys = sorted(list(file_info_dict.keys()))
    latest_log_file_dir = log_file_path + "/MatterTest/" + file_info_dict[keys[-1]]
    logging.info("Folder contain latest logs {}".format(latest_log_file_dir))
    return {"latest_log_file_dir": latest_log_file_dir, "log_file_path": log_file_path}


def separate_logs_iteration_wise():
    log_paths_dict = log_file_finder()
    log_file_directory = log_paths_dict["latest_log_file_dir"]
    fp = open(log_file_directory + "/test_log.INFO")
    data = fp.read()
    fp.close()
    result = re.findall(
        r"(\d+-\d+ \d+:\d+:\d+\.\d+ INFO (\d+) iteration of pairing sequence(.*?)\d+-\d+ \d+:\d+:\d+\.\d+ INFO "
        r"completed pair and unpair sequence for \d+)",
        data, re.DOTALL)
    i = 0
    for res in result:
        i += 1
        fp = open(initializer.log_file_path_iterations + "/iteration_logs_" + str(
            int(i)) + "_" + datetime.datetime.now().isoformat().replace(":", "_").replace(".", "_"), 'w')
        fp.write(res[0])
        fp.close()


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
