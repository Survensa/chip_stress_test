import asyncio
import io
import json
import logging
import os
import select
import shlex
import shutil
import subprocess
import sys
import traceback
import datetime as dt

import yaml
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse

script_executions_stats = {}
html_error = """
            <html>
            <head>
                <title>Log Display Web App</title>
            </head>
            <body>
                <h1>error_message</h1>
            </body>
        </html>
            """

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def config_reader():
    try:
        args = sys.argv
        if len(args) != 0 and "--config" not in args:
            config_yaml_file = os.path.join(os.getcwd(), "config", "config.yaml")
            if not os.path.exists(config_yaml_file):
                logging.error("The config file does not exist! exiting now! ")
                sys.exit(0)
            with io.open(config_yaml_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        elif "--config" in args:
            config_yaml_file = args[1]
            if not os.path.exists(config_yaml_file):
                logging.error("The config file does not exist! exiting now! ")
                sys.exit(0)
            with io.open(config_yaml_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
    except Exception as e:
        logging.error(e)
        traceback.print_exc()


def get_directory_info(dirs_list: list, log_dir: str) -> list:
    """
    this functions takes a list as argument and
    returns only the directory information of last modified,file size, file name, file location,
    in a list of dict objects
    {"dir_name": str,"dir_path":str,
    "dir_last_modified":unix_time, "dir_size":bytes }
    files are ignored and files that do not exist will be ignored
    """
    folder_details_list = []
    for dirs in dirs_list:
        try:
            full_path = os.path.join(log_dir, os.path.join(dirs))
            if not os.path.exists(full_path) or not os.path.isdir(full_path):
                logging.error("the path {} does not exist or is not a directory".format(full_path))
                continue
            stat_obj = os.stat(full_path)
            dir_details = {"dir_name": dirs, "dir_path": full_path,
                           "dir_last_modified": dt.datetime.fromtimestamp(stat_obj.st_mtime).isoformat(),
                           "dir_size": stat_obj.st_size}
            folder_details_list.append(dir_details)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
    folder_details_list = sorted(folder_details_list, key=lambda it: dt.datetime.fromisoformat(it["dir_last_modified"]))
    return folder_details_list


def zip_files(dir_path, dir_name):
    folder_path = os.path.join(dir_path, dir_name)
    if os.path.exists(folder_path):
        try:
            # Attempt to remove the directory and its contents
            logging.info("zipping the files")
            zip_file_path = os.path.join(dir_path, dir_name)
            shutil.make_archive(zip_file_path, 'zip', folder_path)
            logging.info("zipping the files has been completed")
            res = FileResponse(zip_file_path + ".zip", filename=dir_name + ".zip")
            return res
        except Exception as e:
            return {"success": False, "message": "error removing directory internal error"}
    else:
        return {"success": False, "message": "the path does not exist"}


def delete_files(dir_path, dir_name):
    full_path = os.path.join(dir_path, dir_name)
    if os.path.exists(full_path):
        try:
            # Attempt to remove the directory and its contents
            shutil.rmtree(full_path)
            return {"success": True, "message": f"The directory {dir_name} was successfully removed"}

        except Exception as e:
            logging.info(e)
            traceback.print_exc()
            return {"success": False, "message": "error removing directory internal error " + str(e)}
    else:
        return {"success": False, "message": "the path does not exist"}


def execute_bash_script(script_name, script_path, arguments, python_env):
    try:
        logger.info(f"Script '{script_name}' has Started execution ")
        global script_executions_stats
        command = f'{os.getcwd()}/bash_scripts/run_python_script.sh -python_environment {python_env} -script_name {script_name} -script_arguments "{arguments}" -python_script_path {script_path}'
        # Run the script and capture output
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        script_executions_stats.update({script_name: "Script has started execution"})
        timeout_seconds = 60
        while True:
            ready, _, _ = select.select([process.stdout], [], [], timeout_seconds)
            if process.stdout in ready:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if "completed pair and unpair sequence for" in output:
                        logger.info(output)
                        script_executions_stats.update({script_name: output})
            else:
                logger.error("Timeout reached")
                del script_executions_stats[script_name]
                process.kill()
                logger.info(f"Process Is Killed as it became unresponsive!!, can restart {script_name}")
                break

        # Get the return code
        return_code = process.returncode

        if return_code == 0:
            logger.info(f"Script {script_name} executed successfully.")
            del script_executions_stats[script_name]
        else:
            logger.error(f"Script {script_name} execution failed with return code {return_code}.")
            del script_executions_stats[script_name]
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def summary_json_get(path, analytic):
    try:
        fp = open(os.path.join(path, "analytics.json"), "r")
        json_data = json.load(fp)
        fp.close()
        analytic_data = json_data["analytics"].pop(analytic)
        json_data["analytics"] = {analytic: analytic_data}
        return json_data
    except Exception as e:
        logger.error(e)
        return "no data"


def summary_json_find(path):
    runset_children = os.listdir(path)
    # root={"id":"base_path","children":[],"text":"TestCases"}
    data = []
    for run_set_child in runset_children:
        if not os.path.isdir(os.path.join(path, run_set_child)):
            continue
        scripts = os.listdir(os.path.join(path, run_set_child))
        run_set_root = {"id": run_set_child, "text": run_set_child, "children": []}
        for script in scripts:
            if not os.path.isdir(os.path.join(path, run_set_child, script)):
                continue
            iterations = os.listdir(os.path.join(path, run_set_child, script))
            script_root = {"id": f'{run_set_child}**{script}', "text": script, "children": []}
            for iteration in iterations:
                iter_root = {"id": f'{run_set_child}**{script}**{iteration}', "text": iteration, "children": []}
                if os.path.exists(os.path.join(path, run_set_child, script, iteration, "summary.json")):
                    fp = open(os.path.join(path, run_set_child, script, iteration, "summary.json"))
                    analytics = json.load(fp)["analytics_metadata"]
                    fp.close()
                    for analytic in analytics:
                        iter_root["children"].append(
                            {"id": f'{run_set_child}**{script}**{iteration}**{analytic}', "text": analytic.upper()})
                    script_root["children"].append(iter_root)
            run_set_root["children"].append(script_root)
        data.append(run_set_root)
    return data
