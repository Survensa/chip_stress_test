from fabric import Connection
from invoke import UnexpectedExit
import json
import logging



def rpi_reset(data):

       ssh = Connection(host=data['host'], user=data['user'] , connect_kwargs={"password": data['password']})
       
       # Execute 'ps aux | grep process_name' command to find the PID
       command = f"ps aux | grep ./chip-all-clusters-app"
       pid_val = ssh.run(command)

       pid_output = pid_val.stdout
       pid_lines = pid_output.split('\n')
       for line in pid_lines :
         if './chip-all-clusters-app' in line:
            pid = line.split()[1]
            kill_command = f"kill -9 {pid}"
            ssh.run(kill_command)
         break
       logging.info("Example App has been closed")
       ssh.run(' sudo rm -rf /tmp/chip_*')
       ssh.close()


       return True
    
   
def rpi_run(data):

         
          ssh = Connection(host=data['host'], user=data['user'] , connect_kwargs={"password": data['password']})
          path  = data['path']
          try:
              ssh.run( 'cd ' + path +' && ./chip-all-clusters-app ' , hide =True, pty=False)
          except UnexpectedExit as e:
               if e.result.exited == -1:
                    print("Command exited with -1, treating as non-error")
               else:
                    raise
          ssh.close()
          logging.info('Iteration has been completed')

          return True
