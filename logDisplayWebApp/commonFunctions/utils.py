import io
import logging
import os
import shutil
import sys
import traceback
import datetime as dt

import yaml
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse

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


def config_reader():
    try:
        config_yaml_file = os.path.join(os.getcwd(), "config", "config.yaml")
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
            res = FileResponse(zip_file_path+".zip", filename=dir_name + ".zip")
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
            return {"success": False, "message": "error removing directory internal error "+str(e)}
    else:
        return {"success": False, "message": "the path does not exist"}
