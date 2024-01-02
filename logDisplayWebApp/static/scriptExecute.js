function start_script(script_name, script_path) {
  
  var arguments = document.getElementById(script_name).value;
  
  
  if (arguments.length>0){
  arguments.replaceAll(" ",":")
  console.log(arguments)
  var data = { script_name: script_name, script_path: script_path, arguments: arguments }
  fetch("/execute_script", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data)
  })
  .then(function(response){
    if (response.status=200){
      return response.json()
    }
    else {
      alert("server returned status code"+response.status)
    }
  })
  .then(function(data){
      alert(data["message"])
   
  })
  }
  else{
    alert("Arguments filed is empty")
  }
  
}

function showStatus(script_name,script_details){
console.log(script_details)
alert(script_details[script_name]);
}