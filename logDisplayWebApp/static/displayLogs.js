function dutLogsDisplay(dir_path,dir_name,flag){
    window.open("/dutLogs?dir_path="+dir_path+"&dir_name="+dir_name+"&flag="+flag)
}

function enlargedlineChart(dir_path){
    window.open("/loadGraphTemplate?dir_path="+dir_path)
}