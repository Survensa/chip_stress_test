import json
import logging
import os.path
import shutil
import traceback
import datetime
from itertools import islice
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, FileResponse
from fastapi.responses import StreamingResponse

from commonFunctions import utils

app = FastAPI()

# Get the path to the project directory
project_dir = Path(__file__).resolve().parent

# Configure Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(str(project_dir), "templates"))

# Mount static files (e.g., CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(str(project_dir), "static")), name="static")

config = utils.config_reader()


@app.get("/home")
def home_page(request: Request):
    try:
        log_dir = config["logs_path"]
        if not os.path.exists(log_dir):
            error_page = utils.html_error.replace("error_message", "Logs Folder paths does not exist check "
                                                                   "config file")
            return HTMLResponse(content=error_page, status_code=200, )
        dirs = os.listdir(log_dir)
        dir_details = utils.get_directory_info(dirs_list=dirs, log_dir=log_dir)
        return templates.TemplateResponse("index.html", context={
            "request": request,
            "dir_list": dir_details,
            "log_dir": log_dir
        })
    except Exception as e:
        traceback.print_exc()
        return HTMLResponse(content=utils.html_error.replace("error_message", "Internal server error"), status_code=500)


@app.get("/home/test_cases_index")
def test_case_executed(request: Request, dir_path: str):
    dirs = os.listdir(dir_path)
    dir_details = utils.get_directory_info(dirs_list=dirs, log_dir=dir_path)
    for dir_detail in dir_details:
        if os.path.exists(os.path.join(dir_detail["dir_path"], "summary.json")):
            dir_detail.update({"url": "/home/displayLogFolder"})
        else:
            dir_detail.update({"url": "/home/test_cases_index"})
    return templates.TemplateResponse("test_cases_index.html", context={
        "request": request,
        "dir_list": dir_details,
        "log_dir": dir_path,
    })


@app.get("/home/displayLogFolder")
def display_log_folder(request: Request, dir_path: str, page: int = 1, page_size: int = 10,
                       filters: str = "all"):
    dirs_list = os.listdir(dir_path)
    if "summary.json" in dirs_list:
        fp = open(os.path.join(dir_path, "summary.json"), "r")
        summary = json.load(fp)
        fp.close()
        fp = open(os.path.join(dir_path, "analytics.json"), "r")
        analytics_json = json.load(fp)
        fp.close()
        summary["analytics"] = analytics_json["analytics"]
        dir_details = utils.get_directory_info(dirs_list, log_dir=dir_path)
        filtered_data = []
        for row in dir_details:
            if row["dir_name"].isnumeric:
                if int(row["dir_name"]) not in summary["Fail Count"]["Iteration"]:  # pass condition
                    if int(row["dir_name"]) <= summary["number_of_iterations"]:
                        row.update({"iteration_result": "PASS"})
                    else:
                        row.update({"iteration_result": "In-Progress"})
                else:  # fail condition
                    row.update({"iteration_result": "FAIL"})
            if filters == "pass" and row["iteration_result"] == "PASS":
                filtered_data.append(row)
            elif filters == "fail" and row["iteration_result"] == "FAIL":
                filtered_data.append(row)
            elif filters == "all":
                filtered_data.append(row)
            # Paginate the data
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data = list(islice(filtered_data, start_index, end_index))
        # Calculate total pages
        total_pages = (len(filtered_data) + page_size - 1) // page_size

        # Render the Jinja2 template with the paginated and filtered data
        return templates.TemplateResponse(
            "iterAndDutLogs.html",
            {
                "request": request,
                "table_data": paginated_data,
                "current_page": page,
                "total_pages": total_pages,
                "current_page_size": page_size,
                "current_filter": filters,
                "dir_path": dir_path,
                "summary": summary
            },
        )
    else:
        dir_details = utils.get_directory_info(dirs_list, log_dir=dir_path)
        filtered_data = dir_details.copy()
        # Paginate the data
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data = list(islice(filtered_data, start_index, end_index))
        # Calculate total pages
        total_pages = (len(filtered_data) + page_size - 1) // page_size
        summary = {
            "Pass Count": "NA",
            "Fail Count": {
                "Count": "NA",
                "Iteration": "NA"
            },
            "Error Count": "NA",
            "Failed_iteration_details": "NA",
            "pairing_duration_info": {
            },
            "platform": "NA",
            "number_of_iterations": "NA",
            "commissioning_method": "NA",
            "execution_mode": "NA"
        }
        # Render the Jinja2 template with the paginated and filtered data
        return templates.TemplateResponse(
            "iterAndDutLogs.html",
            {
                "request": request,
                "table_data": paginated_data,
                "current_page": page,
                "total_pages": total_pages,
                "current_page_size": page_size,
                "current_filter": filters,
                "dir_path": dir_path,
                "summary": summary
            },
        )


@app.get("/logFileOperations")
def delete_or_zip_files(dir_path: str, flag: str, dir_name):
    try:
        if flag == "zip":
            file_resp = utils.zip_files(dir_path, dir_name)
            return file_resp
        elif flag == "delete":
            del_resp = utils.delete_files(dir_path, dir_name)
            return del_resp
        else:
            return HTMLResponse(content=utils.html_error.replace("error_message", "Invalid operation"),
                                status_code=200)
    except Exception as e:
        traceback.print_exc()
        return HTMLResponse(content=utils.html_error.replace("error_message", "Internal server error"), status_code=500)


@app.get("/get_log_contents")
def send_log_files(request: Request, file_path: str, file_name: str):
    file = os.path.join(file_path, file_name)
    return StreamingResponse(file_serve(file), media_type="text/plain")


def file_serve(file):  #
    with open(file, mode="rb") as file_like:  #
        yield from file_like


@app.get("/dutLogs")
async def dut_logs_find(request: Request, dir_path: str, dir_name: str, flag: str):
    full_path = os.path.join(dir_path, dir_name)
    files = []
    for filename in os.listdir(full_path):
        if 'dut' in filename.lower() and flag == "dut":
            file_details = {
                "file_name": filename,
                "file_path": full_path,
                "file_size": os.path.getsize(os.path.join(full_path, filename)),
                "file_last_modified": datetime.datetime.fromtimestamp(
                    os.stat(os.path.join(full_path, filename)).st_mtime)
            }
            files.append(file_details)
        elif 'dut' not in filename.lower() and flag == "iter":
            file_details = {
                "file_name": filename,
                "file_path": full_path,
                "file_size": os.path.getsize(os.path.join(full_path, filename)),
                "file_last_modified": datetime.datetime.fromtimestamp(
                    os.stat(os.path.join(full_path, filename)).st_mtime)
            }
            files.append(file_details)
    files = sorted(files, key=lambda it: it["file_last_modified"])
    if len(files) > 1:
        return templates.TemplateResponse(
            "LogSelect.html",
            {
                "request": request,
                "files": files,
                "numberOfFiles": len(files),
                "file_path": full_path
            },
        )
    else:
        file = os.path.join(full_path, files[0]["file_name"])
        return StreamingResponse(file_serve(file), media_type="text/plain")


@app.get('/loadGraphTemplate')
def load_graph_template(request: Request, dir_path: str):
    dirs_list = os.listdir(dir_path)
    if "summary.json" not in dirs_list:
        return HTMLResponse(content=utils.html_error.replace("error_message",
                                                             "This folder does not contain logs choose other folders"),
                            status_code=200)
    fp = open(os.path.join(dir_path, "summary.json"), "r")
    summary = json.load(fp)
    fp.close()
    fp = open(os.path.join(dir_path, "analytics.json"), "r")
    analytics = json.load(fp)
    fp.close()
    summary.update({"analytics": analytics["analytics"]})
    return templates.TemplateResponse("enlargedGraph.html", {"request": request, "summary_json": summary})


@app.get("/scriptExecution")
def render_script_execution_page(request: Request):
    script_path = config["script_path"]
    script_names = os.listdir(script_path)
    script_names = [python_file for python_file in script_names if ".py" in python_file]
    return templates.TemplateResponse("testScriptDisplay.html",
                                      {"request": request,
                                       "script_names": script_names,
                                       "script_path": script_path,
                                       "script_exe_details": utils.script_executions_stats})


@app.post("/execute_script")
def start_script(script_execution_details: dict, background_tasks: BackgroundTasks):
    try:
        script_name = script_execution_details["script_name"]
        script_path = script_execution_details["script_path"]
        arguments = script_execution_details["arguments"].replace(" ", ":-:")
        if script_name in utils.script_executions_stats.keys():
            return {"success": True, "message": f"The execution {script_name} script has been started already !!!!!"}
        background_tasks.add_task(utils.execute_bash_script, script_name=script_name,
                                  script_path=script_path,
                                  arguments=arguments,
                                  python_env=config["python_environment"])
        return {"success": True, "message": "Script Execution has Started"}
    except Exception as e:
        logging.error(e)
        return {"success": True, "message": str(e)}


@app.get("/compareScriptAnalytics")
def compare_script_analytics(request: Request):
    log_dir = config["logs_path"]
    if not os.path.exists(log_dir):
        error_page = utils.html_error.replace("error_message", "Logs Folder paths does not exist check "
                                                               "config file")
        return HTMLResponse(content=error_page, status_code=200, )
    graph_options = utils.summary_json_find(log_dir)
    return templates.TemplateResponse("compareScriptAnalytics.html", {
        "request": request,
        "test_case_details": {"graph_options": graph_options, "base_path": log_dir}
    })


@app.post("/compareGraphData")
def compare_graph_data(fetch_data: dict, request: Request):
    response_dict = {}
    log_dir = config["logs_path"]
    graph_parameter_list = []
    for selected_data in fetch_data["fetch_data"]:
        path_with_para = selected_data.split("**")
        parameter = path_with_para.pop(-1)
        path = os.path.join(log_dir, *path_with_para)
        response_dict.update({parameter: []})
        graph_parameter_list.append({"analytics": parameter,
                                     "full_path": path,
                                     "iteration": "|  |".join(path_with_para),
                                     "script_name": path_with_para[1]})
    for graph in graph_parameter_list:
        summary_json = utils.summary_json_get(graph["full_path"], graph["analytics"])
        if summary_json != "no data":
            analytics_data = summary_json["analytics"][graph["analytics"]]
            for data in analytics_data.items():
                response_dict[graph["analytics"]].append(
                    {"iteration_number": data[0], "value": data[1], "iteration": graph["iteration"]})
        else:
            response_dict[graph["analytics"]].append("no data")
    return response_dict


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run(host=config["host"], port=config["port"], app="LogDisplay:app", workers=config["workers"])
