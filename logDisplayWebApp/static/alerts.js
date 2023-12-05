
    function showCustomDialog(dir_path,dir_name) {
        // Show the custom dialog and overlay
        document.getElementById('customDialog').style.display = 'block';
        document.getElementById('overlay').style.display = 'block';
        document.getElementById('ok').addEventListener('click', function() {
        performDelete(dir_path,dir_name);
        document.getElementById('ok').removeEventListener('click', arguments.callee);
    });
    document.getElementById('cancel').addEventListener('click', function() {
        hideCustomDialog();
        document.getElementById('cancel').removeEventListener('click', arguments.callee);
    });
    }

    function hideCustomDialog() {
        // Hide the custom dialog and overlay
        document.getElementById('customDialog').style.display = 'none';
        document.getElementById('overlay').style.display = 'none';
    }

    function performDelete(dir_path,dir_name) {
        // Replace this with your actual delete logic
       fetch("/logFileOperations?dir_path="+dir_path+"&dir_name="+dir_name+"&flag=delete")
                .then(
                response => response.json())
                .then(data=>{
                    if (data.success) {
                    alert(data.message);
                    location.reload()
                    }
                    else{
                    alert(data.message);
                    location.reload()
                    }
                })
                .catch(error => {
                console.error('Error fetching details:', error);
                alert("Error from script "+String(error))
            })

    }

    function cancelDelete() {
        // Handle cancellation or provide feedback
        alert("Delete operation canceled.");
        hideCustomDialog();
    }
    function fileFetch(dir_path,dir_name,flag){
            url="/logFileOperations?dir_path="+dir_path+"&dir_name="+dir_name+"&flag="+flag
            if (flag=="zip"){
                window.open(url)
            }
            else{
            showCustomDialog(dir_path,dir_name);
            }

        }
